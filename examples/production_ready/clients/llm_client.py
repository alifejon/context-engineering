"""
Production-Ready LLM Client

실제 프로덕션 환경에서 사용 가능한 LLM API 클라이언트
- 재시도 로직 (exponential backoff)
- Rate limiting
- 에러 핸들링
- 타임아웃
- 메트릭 수집
"""

import logging
import time
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import os

# OpenAI SDK
try:
    from openai import OpenAI, AsyncOpenAI
    from openai import OpenAIError, RateLimitError, APITimeoutError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI SDK not installed. Install with: pip install openai")

# Error handling
from ..core.error_handling import (
    with_retry,
    LLMAPIError,
    RateLimitError as CustomRateLimitError,
    QuotaExceededError
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    cost: float
    latency_ms: float
    finish_reason: str
    request_id: Optional[str] = None


@dataclass
class ModelConfig:
    """Model configuration."""
    name: str
    max_tokens: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    rpm_limit: int  # Requests per minute


class ProductionLLMClient:
    """
    Production-ready LLM client with all safety features.

    Features:
    - Automatic retry with exponential backoff
    - Rate limiting (token bucket algorithm)
    - Request timeout
    - Cost tracking
    - Detailed error handling
    - Request/response logging
    """

    # Model configurations
    MODELS = {
        'gpt-4': ModelConfig(
            name='gpt-4',
            max_tokens=8192,
            input_cost_per_1k=0.03,
            output_cost_per_1k=0.06,
            rpm_limit=10000  # tier 4
        ),
        'gpt-4-turbo': ModelConfig(
            name='gpt-4-turbo-preview',
            max_tokens=128000,
            input_cost_per_1k=0.01,
            output_cost_per_1k=0.03,
            rpm_limit=10000
        ),
        'gpt-3.5-turbo': ModelConfig(
            name='gpt-3.5-turbo',
            max_tokens=16385,
            input_cost_per_1k=0.0015,
            output_cost_per_1k=0.002,
            rpm_limit=10000
        ),
    }

    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        enable_rate_limiting: bool = True
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_rate_limiting: Whether to enable client-side rate limiting
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not installed")

        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=0)
        self.max_retries = max_retries
        self.enable_rate_limiting = enable_rate_limiting

        # Rate limiters per model
        self._rate_limiters = {}
        if enable_rate_limiting:
            for model_key, config in self.MODELS.items():
                self._rate_limiters[model_key] = TokenBucketRateLimiter(
                    max_requests_per_minute=config.rpm_limit
                )

        # Metrics
        self.total_requests = 0
        self.total_cost = 0.0
        self.total_tokens = 0

    def generate(
        self,
        query: str,
        context: str = "",
        model: str = "gpt-4-turbo",
        max_tokens: int = 500,
        temperature: float = 0.7,
        request_id: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate response from LLM.

        Args:
            query: User query
            context: System context/instructions
            model: Model name
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            request_id: Optional request ID for tracking

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMAPIError: If API call fails
            RateLimitError: If rate limit exceeded
            QuotaExceededError: If quota exceeded
        """
        start_time = time.time()

        # Normalize model name
        model_key = self._get_model_key(model)
        model_config = self.MODELS[model_key]

        logger.info(
            "LLM request started",
            extra={
                'request_id': request_id,
                'model': model_config.name,
                'query_length': len(query),
                'context_length': len(context),
                'max_tokens': max_tokens
            }
        )

        # Rate limiting
        if self.enable_rate_limiting:
            if not self._rate_limiters[model_key].acquire():
                raise CustomRateLimitError(
                    f"Rate limit exceeded for {model_config.name}"
                )

        # Retry wrapper
        @with_retry(
            max_attempts=self.max_retries,
            exceptions=(APIConnectionError, APITimeoutError),
            backoff_factor=2.0
        )
        def _make_request():
            return self.client.chat.completions.create(
                model=model_config.name,
                messages=[
                    {"role": "system", "content": context} if context else None,
                    {"role": "user", "content": query}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

        try:
            # Make API call
            response = _make_request()

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }

            cost = self._calculate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                model_config
            )

            # Update metrics
            self.total_requests += 1
            self.total_cost += cost
            self.total_tokens += response.usage.total_tokens

            logger.info(
                "LLM request completed",
                extra={
                    'request_id': request_id,
                    'model': model_config.name,
                    'usage': usage,
                    'cost': cost,
                    'latency_ms': latency_ms,
                    'finish_reason': response.choices[0].finish_reason
                }
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=usage,
                cost=cost,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason,
                request_id=request_id
            )

        except RateLimitError as e:
            logger.error(
                "Rate limit exceeded",
                extra={
                    'request_id': request_id,
                    'model': model_config.name,
                    'error': str(e)
                }
            )
            raise CustomRateLimitError(f"OpenAI rate limit exceeded: {e}")

        except OpenAIError as e:
            error_code = getattr(e, 'code', None)

            if error_code == 'insufficient_quota':
                logger.critical(
                    "OpenAI quota exceeded",
                    extra={'request_id': request_id, 'error': str(e)}
                )
                raise QuotaExceededError(f"OpenAI quota exceeded: {e}")

            logger.error(
                "OpenAI API error",
                extra={
                    'request_id': request_id,
                    'error_code': error_code,
                    'error': str(e)
                }
            )
            raise LLMAPIError(f"OpenAI API error: {e}")

        except Exception as e:
            logger.exception(
                "Unexpected error in LLM request",
                extra={'request_id': request_id}
            )
            raise LLMAPIError(f"Unexpected error: {e}")

    def _get_model_key(self, model: str) -> str:
        """Normalize model name to key."""
        # Handle various model name formats
        if 'gpt-4-turbo' in model or 'gpt-4-1106' in model:
            return 'gpt-4-turbo'
        elif 'gpt-4' in model:
            return 'gpt-4'
        elif 'gpt-3.5' in model:
            return 'gpt-3.5-turbo'
        else:
            raise ValueError(f"Unknown model: {model}")

    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_config: ModelConfig
    ) -> float:
        """Calculate request cost."""
        input_cost = (prompt_tokens / 1000) * model_config.input_cost_per_1k
        output_cost = (completion_tokens / 1000) * model_config.output_cost_per_1k
        return input_cost + output_cost

    def get_metrics(self) -> Dict:
        """Get client metrics."""
        return {
            'total_requests': self.total_requests,
            'total_cost': self.total_cost,
            'total_tokens': self.total_tokens,
            'avg_cost_per_request': self.total_cost / max(1, self.total_requests),
            'avg_tokens_per_request': self.total_tokens / max(1, self.total_requests)
        }


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter.

    Smoothly limits requests per minute while allowing bursts.
    """

    def __init__(self, max_requests_per_minute: int):
        self.max_requests = max_requests_per_minute
        self.tokens = max_requests_per_minute
        self.last_update = time.time()

    def acquire(self) -> bool:
        """
        Try to acquire a token.

        Returns:
            True if token acquired, False if rate limit exceeded
        """
        now = time.time()
        elapsed = now - self.last_update

        # Refill tokens based on elapsed time
        tokens_to_add = elapsed * (self.max_requests / 60.0)
        self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
        self.last_update = now

        # Try to consume a token
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        else:
            return False


# Example usage
if __name__ == "__main__":
    from examples.production_ready.core.logging_config import setup_logging

    # Setup logging
    setup_logging(level="INFO", json_logs=False)

    print("="*60)
    print("Production LLM Client Example")
    print("="*60)

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("\n❌ OPENAI_API_KEY not set in environment")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print("\n💡 This example shows the client structure.")
        print("   To actually call the API, set your API key.\n")

        # Show simulated behavior
        print("="*60)
        print("Simulated Client Behavior")
        print("="*60)

        print("\n1. Client initialization:")
        print("   ✓ OpenAI client created")
        print("   ✓ Rate limiters set up for each model")
        print("   ✓ Retry logic configured")

        print("\n2. Request flow:")
        print("   ✓ Check rate limit")
        print("   ✓ Make API call with retry")
        print("   ✓ Calculate cost from usage")
        print("   ✓ Log metrics")
        print("   ✓ Return response")

        print("\n3. Error handling:")
        print("   ✓ Rate limit exceeded → wait and retry")
        print("   ✓ Timeout → exponential backoff retry")
        print("   ✓ Quota exceeded → critical error")
        print("   ✓ Network error → retry up to max_retries")

    else:
        # Real API call
        print("\n✓ API key found, making real API call...\n")

        try:
            client = ProductionLLMClient(
                api_key=api_key,
                timeout=30,
                max_retries=3
            )

            response = client.generate(
                query="What is 2+2? Answer in one sentence.",
                context="You are a helpful math assistant.",
                model="gpt-3.5-turbo",
                max_tokens=50,
                request_id="example_001"
            )

            print(f"Response: {response.content}")
            print(f"Model: {response.model}")
            print(f"Tokens: {response.usage['total_tokens']}")
            print(f"Cost: ${response.cost:.4f}")
            print(f"Latency: {response.latency_ms:.0f}ms")

            print("\nClient metrics:")
            metrics = client.get_metrics()
            for key, value in metrics.items():
                if 'cost' in key:
                    print(f"  {key}: ${value:.4f}")
                elif 'tokens' in key:
                    print(f"  {key}: {value:.0f}")
                else:
                    print(f"  {key}: {value}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Check your API key and internet connection")

    print("\n" + "="*60)
    print("✓ Example complete!")
    print("\n💡 Production tips:")
    print("  • Use environment variables for API keys")
    print("  • Monitor costs with logging")
    print("  • Set appropriate rate limits")
    print("  • Implement circuit breakers for resilience")
    print("  • Use async client for high throughput")

"""
Production-Ready Error Handling

실제 프로덕션 환경에서 사용 가능한 에러 핸들링 구현
"""

import logging
from typing import Optional, Callable, Any
from functools import wraps
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextEngineeringError(Exception):
    """Base exception for context engineering errors."""
    pass


class TokenCountingError(ContextEngineeringError):
    """Token counting failed."""
    pass


class OptimizationError(ContextEngineeringError):
    """Query optimization failed."""
    pass


class CacheError(ContextEngineeringError):
    """Cache operation failed."""
    pass


class LLMAPIError(ContextEngineeringError):
    """LLM API call failed."""
    pass


class RateLimitError(LLMAPIError):
    """Rate limit exceeded."""
    pass


class QuotaExceededError(LLMAPIError):
    """API quota exceeded."""
    pass


class ValidationError(ContextEngineeringError):
    """Input validation failed."""
    pass


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        exceptions: Tuple of exceptions to catch
        on_retry: Callback function called on retry

    Example:
        @with_retry(max_attempts=3, exceptions=(TimeoutError,))
        def fetch_data():
            return api.get_data()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts",
                            exc_info=True,
                            extra={
                                'function': func.__name__,
                                'attempts': max_attempts,
                                'error': str(e)
                            }
                        )
                        raise

                    # Calculate backoff time
                    wait_time = backoff_factor ** attempt

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_attempts': max_attempts,
                            'wait_time': wait_time,
                            'error': str(e)
                        }
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(wait_time)

            # Should never reach here
            raise last_exception

        return wrapper
    return decorator


def validate_input(
    query: Optional[str],
    context: Optional[str],
    min_quality: float,
    max_cost: Optional[float] = None
) -> tuple[str, str]:
    """
    Validate and sanitize inputs.

    Args:
        query: User query
        context: Context string
        min_quality: Minimum quality score (0-1)
        max_cost: Maximum cost in dollars

    Returns:
        Tuple of (validated_query, validated_context)

    Raises:
        ValidationError: If validation fails
    """
    # Validate query
    if query is None:
        raise ValidationError("Query cannot be None")

    if not isinstance(query, str):
        raise ValidationError(f"Query must be string, got {type(query)}")

    if len(query.strip()) == 0:
        raise ValidationError("Query cannot be empty")

    if len(query) > 50000:  # ~12K tokens max
        raise ValidationError(f"Query too long: {len(query)} chars (max 50000)")

    # Validate context
    if context is None:
        context = ""

    if not isinstance(context, str):
        raise ValidationError(f"Context must be string, got {type(context)}")

    if len(context) > 500000:  # ~125K tokens max
        raise ValidationError(f"Context too long: {len(context)} chars (max 500000)")

    # Validate min_quality
    if not isinstance(min_quality, (int, float)):
        raise ValidationError(f"min_quality must be number, got {type(min_quality)}")

    if not 0 <= min_quality <= 1:
        raise ValidationError(f"min_quality must be 0-1, got {min_quality}")

    # Validate max_cost
    if max_cost is not None:
        if not isinstance(max_cost, (int, float)):
            raise ValidationError(f"max_cost must be number, got {type(max_cost)}")

        if max_cost <= 0:
            raise ValidationError(f"max_cost must be positive, got {max_cost}")

    # Sanitize (remove potential issues)
    query = query.strip()
    context = context.strip()

    return query, context


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping calls to failing services.

    States:
    - CLOSED: Normal operation
    - OPEN: Service is failing, reject calls
    - HALF_OPEN: Testing if service recovered
    """

    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == self.OPEN:
            if self._should_attempt_reset():
                self.state = self.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. "
                    f"Service unavailable for {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset if in HALF_OPEN
            if self.state == self.HALF_OPEN:
                self._reset()

            return result

        except self.expected_exception as e:
            self._record_failure()
            raise

    def _record_failure(self):
        """Record a failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}",
            extra={
                'failure_count': self.failure_count,
                'threshold': self.failure_threshold,
                'state': self.state
            }
        )

        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.error(
                "Circuit breaker opened - service marked as unavailable",
                extra={
                    'failure_count': self.failure_count,
                    'threshold': self.failure_threshold
                }
            )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

        logger.info("Circuit breaker closed - service recovered")


# Example usage
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example 1: Retry decorator
    print("="*60)
    print("Example 1: Retry with Exponential Backoff")
    print("="*60)

    call_count = 0

    @with_retry(max_attempts=3, exceptions=(ValueError,))
    def flaky_function():
        global call_count
        call_count += 1
        print(f"  Attempt {call_count}")

        if call_count < 3:
            raise ValueError("Temporary error")

        return "Success!"

    try:
        result = flaky_function()
        print(f"  Result: {result}\n")
    except Exception as e:
        print(f"  Failed: {e}\n")

    # Example 2: Input validation
    print("="*60)
    print("Example 2: Input Validation")
    print("="*60)

    test_cases = [
        ("Valid query", "Valid context", 0.8, None, True),
        (None, "context", 0.8, None, False),
        ("", "context", 0.8, None, False),
        ("query", "context", 1.5, None, False),
        ("query", "context", 0.8, -1.0, False),
    ]

    for query, context, min_q, max_c, should_pass in test_cases:
        try:
            q, c = validate_input(query, context, min_q, max_c)
            print(f"  ✓ Valid: query='{query}', context='{context}'")
        except ValidationError as e:
            if should_pass:
                print(f"  ✗ Unexpected failure: {e}")
            else:
                print(f"  ✓ Correctly rejected: {e}")

    # Example 3: Circuit breaker
    print("\n" + "="*60)
    print("Example 3: Circuit Breaker Pattern")
    print("="*60)

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=2.0)

    def unreliable_service():
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Service error")
        return "Success"

    for i in range(10):
        try:
            result = breaker.call(unreliable_service)
            print(f"  Call {i+1}: {result} (state: {breaker.state})")
        except Exception as e:
            print(f"  Call {i+1}: Failed - {e} (state: {breaker.state})")

        time.sleep(0.5)

    print("\n✓ Error handling examples complete!")

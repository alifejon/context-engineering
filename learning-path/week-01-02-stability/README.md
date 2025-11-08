# Week 1-2: Foundation & Stability

## 개요

프로덕션 시스템의 가장 중요한 기초: **안정성과 관찰성**을 구축합니다.

**학습 목표**:
- ✅ 모든 에러를 우아하게 처리
- ✅ 시스템의 모든 동작을 추적 가능하게 로깅
- ✅ 테스트로 품질 보장
- ✅ CI/CD로 자동화

**예상 시간**: 40시간 (주당 20시간)

## Day 1-2: Error Handling (12시간)

### 학습 목표
프로덕션 환경에서 발생하는 모든 에러를 안전하게 처리합니다.

### 이론 (2시간)

#### 왜 에러 핸들링이 중요한가?

```python
# ❌ 교육용 코드
def optimize_query(query, context):
    tokens = count_tokens(query + context)
    cost = calculate_cost(tokens, "gpt-4")
    return {"tokens": tokens, "cost": cost}

# 문제:
# 1. query가 None이면? → TypeError
# 2. tiktoken API 실패하면? → 전체 시스템 다운
# 3. 네트워크 오류면? → 요청 실패
```

```python
# ✅ 프로덕션 코드
from tenacity import retry, stop_after_attempt, wait_exponential

def optimize_query(query: str, context: str) -> dict:
    # 1. 입력 검증
    if not query:
        raise ValueError("Query cannot be empty")

    # 2. 재시도 with exponential backoff
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _count_with_retry():
        try:
            return count_tokens(query + context)
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            raise

    # 3. Fallback logic
    try:
        tokens = _count_with_retry()
    except Exception:
        # Approximate token count
        tokens = len((query + context).split()) * 1.3
        logger.error("Using approximate token count")

    cost = calculate_cost(tokens, "gpt-4")
    return {"tokens": tokens, "cost": cost}
```

#### 핵심 패턴

**1. Retry Pattern (재시도)**
```python
from examples.production_ready.core.error_handling import with_retry

@with_retry(max_attempts=3, backoff_factor=2.0)
def call_external_api():
    return api.fetch_data()

# 실패 시:
# Attempt 1: 즉시
# Attempt 2: 2초 후
# Attempt 3: 4초 후
# Attempt 4: 8초 후
```

**2. Circuit Breaker (회로 차단기)**
```python
from examples.production_ready.core.error_handling import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,  # 5번 실패 시
    recovery_timeout=60   # 60초 동안 차단
)

try:
    result = breaker.call(unreliable_service.fetch)
except Exception:
    # Circuit OPEN - use fallback
    result = cached_data
```

**3. Input Validation (입력 검증)**
```python
from examples.production_ready.core.error_handling import validate_input

try:
    query, context = validate_input(
        query=user_input,
        context=doc_context,
        min_quality=0.8,
        max_cost=1.0
    )
except ValidationError as e:
    return {"error": str(e)}, 400
```

### 실습 (8시간)

#### Exercise 1: Retry Logic 구현 (2시간)

**과제**: OpenAI API 호출에 재시도 로직 추가

```python
# exercises/01_retry_logic.py

import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """
    TODO: 구현하세요

    요구사항:
    1. max_attempts만큼 재시도
    2. 매 재시도마다 delay를 backoff_factor배 증가
    3. 마지막 시도 실패 시 예외 발생
    4. 각 시도를 로깅

    힌트:
    - for loop 사용
    - time.sleep() 사용
    - try/except로 예외 처리
    """
    pass  # 구현하세요


# 테스트
call_count = 0

def flaky_api_call():
    global call_count
    call_count += 1
    if call_count < 3:
        raise Exception("API Error")
    return "Success"

result = retry_with_backoff(flaky_api_call)
print(f"Result: {result}")
print(f"Attempts: {call_count}")

# 예상 출력:
# Attempt 1 failed: API Error (waiting 1.0s)
# Attempt 2 failed: API Error (waiting 2.0s)
# Attempt 3 succeeded
# Result: Success
# Attempts: 3
```

**검증**:
```bash
python exercises/01_retry_logic.py
pytest tests/test_retry_logic.py -v
```

#### Exercise 2: Circuit Breaker 구현 (3시간)

**과제**: Circuit breaker 패턴 구현

```python
# exercises/02_circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class SimpleCircuitBreaker:
    def __init__(self, failure_threshold: int, timeout_seconds: int):
        """
        TODO: 구현하세요

        요구사항:
        1. CLOSED: 정상 동작
        2. failure_threshold 초과 시 OPEN
        3. timeout_seconds 후 HALF_OPEN
        4. HALF_OPEN에서 성공 시 CLOSED
        5. HALF_OPEN에서 실패 시 다시 OPEN
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        # TODO: 필요한 변수 초기화

    def call(self, func):
        """
        TODO: 구현하세요

        로직:
        1. state가 OPEN이면 즉시 예외
        2. state가 HALF_OPEN이면 한 번 시도
        3. state가 CLOSED이면 정상 호출
        """
        pass


# 테스트
breaker = SimpleCircuitBreaker(failure_threshold=3, timeout_seconds=5)

def failing_service():
    raise Exception("Service Down")

# Circuit이 열리는지 테스트
for i in range(5):
    try:
        breaker.call(failing_service)
    except Exception as e:
        print(f"Call {i+1}: {e}, State: {breaker.state}")
```

**검증**:
```bash
python exercises/02_circuit_breaker.py
pytest tests/test_circuit_breaker.py -v
```

#### Exercise 3: Input Validation (2시간)

**과제**: 사용자 입력 검증 함수 작성

```python
# exercises/03_input_validation.py

from typing import Tuple

class ValidationError(Exception):
    pass

def validate_optimization_request(
    query: str,
    context: str,
    min_quality: float,
    max_cost: float
) -> Tuple[str, str]:
    """
    TODO: 구현하세요

    검증 규칙:
    1. query:
       - None 불가
       - 빈 문자열 불가
       - 길이 < 10,000자
    2. context:
       - None일 경우 빈 문자열로
       - 길이 < 100,000자
    3. min_quality:
       - 0.0 ~ 1.0 범위
    4. max_cost:
       - 양수

    Returns:
        (sanitized_query, sanitized_context)

    Raises:
        ValidationError: 검증 실패 시
    """
    pass


# 테스트 케이스
test_cases = [
    # (query, context, min_q, max_c, should_pass)
    ("Valid query", "Valid context", 0.8, 1.0, True),
    (None, "context", 0.8, 1.0, False),
    ("", "context", 0.8, 1.0, False),
    ("query", "context", 1.5, 1.0, False),
    ("query", "context", 0.8, -1.0, False),
]

for query, context, min_q, max_c, should_pass in test_cases:
    try:
        q, c = validate_optimization_request(query, context, min_q, max_c)
        if should_pass:
            print(f"✓ Passed: {query}")
        else:
            print(f"✗ Should have failed: {query}")
    except ValidationError as e:
        if not should_pass:
            print(f"✓ Correctly rejected: {e}")
        else:
            print(f"✗ Should have passed: {e}")
```

**검증**:
```bash
python exercises/03_input_validation.py
pytest tests/test_input_validation.py -v
```

#### Exercise 4: 통합 - Production LLM Client (1시간)

**과제**: 모든 패턴을 결합한 LLM 클라이언트

```python
# exercises/04_production_client.py

from examples.production_ready.core.error_handling import (
    with_retry,
    validate_input,
    CircuitBreaker
)

class ProductionOptimizer:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    def optimize(self, query: str, context: str, min_quality: float = 0.8):
        """
        TODO: 구현하세요

        1. validate_input()로 입력 검증
        2. Circuit breaker로 보호
        3. with_retry로 재시도
        4. 에러 시 로깅
        5. Fallback 로직
        """
        pass


# 사용 예
optimizer = ProductionOptimizer()

try:
    result = optimizer.optimize(
        query="What is context engineering?",
        context="...",
        min_quality=0.8
    )
    print(f"Success: {result}")
except Exception as e:
    print(f"Failed: {e}")
```

### 프로젝트 과제 (2시간)

**미니 프로젝트**: "Resilient Context Optimizer"

요구사항:
1. 입력 검증
2. 재시도 로직 (3회)
3. Circuit breaker
4. 에러 타입별 처리:
   - `ValidationError` → 400 응답
   - `RateLimitError` → 429 응답, 재시도
   - `QuotaExceededError` → 503 응답, 알람
   - 기타 → 500 응답, 로깅
5. 테스트 작성 (pytest)

```python
# project/resilient_optimizer.py

class ResilientOptimizer:
    """
    프로덕션 수준의 견고한 optimizer
    """
    def __init__(self):
        # TODO: 초기화
        pass

    def optimize(self, query: str, context: str) -> dict:
        # TODO: 구현
        pass

    def get_health_status(self) -> dict:
        """Circuit breaker 상태 등 반환"""
        pass
```

**검증**:
```bash
pytest project/test_resilient_optimizer.py -v --cov
# Coverage > 80% 목표
```

## Day 3-4: Structured Logging (8시간)

### 학습 목표
모든 시스템 동작을 추적 가능하게 만듭니다.

### 이론 (1시간)

#### print() vs Logging

```python
# ❌ 프로덕션 불가
def process_query(query):
    print(f"Processing: {query}")
    result = optimize(query)
    print(f"Result: {result}")
    return result

# 문제:
# 1. 로그 레벨 없음 (DEBUG vs ERROR 구분 불가)
# 2. 구조화 안됨 (파싱 어려움)
# 3. 파일 저장 안됨
# 4. 요청 추적 불가
```

```python
# ✅ 프로덕션 로깅
import logging
import structlog

logger = structlog.get_logger()

def process_query(query: str, request_id: str):
    logger.info(
        "query_processing_started",
        request_id=request_id,
        query_length=len(query),
        timestamp=datetime.utcnow()
    )

    try:
        result = optimize(query)

        logger.info(
            "query_processing_completed",
            request_id=request_id,
            tokens_used=result['tokens'],
            cost=result['cost']
        )

        return result

    except Exception as e:
        logger.error(
            "query_processing_failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise
```

### 실습 (5시간)

#### Exercise 5: JSON 로깅 설정 (2시간)

```python
# exercises/05_json_logging.py

from examples.production_ready.core.logging_config import setup_logging
import logging

# TODO: JSON 로깅 설정
setup_logging(level="INFO", json_logs=True)

logger = logging.getLogger(__name__)

# TODO: 다음 정보를 로깅하세요
# 1. 요청 시작 (request_id, user_id, endpoint)
# 2. 토큰 카운팅 (tokens, model)
# 3. 비용 계산 (cost, currency)
# 4. 응답 (latency_ms, status_code)

def process_request(request_id: str, user_id: str, query: str):
    """
    TODO: 구조화된 로깅 구현
    """
    pass
```

**검증**:
```bash
python exercises/05_json_logging.py > output.log
cat output.log | jq .  # JSON 파싱 확인
```

#### Exercise 6: Request Logger (2시간)

```python
# exercises/06_request_logger.py

from examples.production_ready.core.logging_config import RequestLogger
import logging

class APIEndpoint:
    def __init__(self):
        self.base_logger = logging.getLogger(__name__)

    def handle_request(self, request_id: str, data: dict):
        # TODO: RequestLogger 사용
        # 모든 로그에 request_id 자동 포함

        request_logger = RequestLogger(self.base_logger, request_id)

        request_logger.info("Request received", data=data)

        # Process...

        request_logger.info("Processing complete", result="...")

        return result
```

#### Exercise 7: Metrics Logger (1시간)

```python
# exercises/07_metrics_logger.py

from examples.production_ready.core.logging_config import MetricsLogger
import logging

metrics_logger = MetricsLogger(logging.getLogger("metrics"))

def optimize_with_metrics(query: str, context: str, request_id: str):
    """
    TODO: 메트릭 로깅 추가

    로깅할 메트릭:
    1. query_metrics: tokens, cost, latency
    2. optimization_metrics: compression_ratio
    3. cache_metrics: hit/miss
    """
    pass
```

### 프로젝트 과제 (2시간)

**미니 프로젝트**: "Observable Optimizer"

요구사항:
1. JSON 구조화 로깅
2. Request ID 추적
3. 메트릭 로깅
4. 에러 로깅 (stack trace 포함)
5. 로그 파일 rotation

```python
# project/observable_optimizer.py

from examples.production_ready.core.logging_config import (
    setup_logging,
    RequestLogger,
    MetricsLogger
)

class ObservableOptimizer:
    def __init__(self):
        setup_logging(level="INFO", json_logs=True, log_file="optimizer.log")
        # TODO: 초기화

    def optimize(self, query: str, context: str, request_id: str) -> dict:
        # TODO: 모든 단계 로깅
        pass
```

**검증**:
```bash
python project/observable_optimizer.py
cat optimizer.log | jq '.level' | sort | uniq -c
# INFO, WARNING, ERROR 레벨 확인
```

## Day 5-7: Testing (20시간)

### 학습 목표
테스트로 코드 품질을 보장합니다.

### 이론 (2시간)

#### 테스트 피라미드

```
       /\
      /E2E\         10% - End-to-end tests
     /------\
    /Integra\       20% - Integration tests
   /----------\
  /Unit Tests \     70% - Unit tests
 /--------------\
```

#### 핵심 개념

**1. Unit Test (단위 테스트)**
```python
# tests/test_validation.py

def test_validate_input_success():
    """정상 입력은 통과"""
    query, context = validate_input("query", "context", 0.8, 1.0)
    assert query == "query"
    assert context == "context"

def test_validate_input_empty_query():
    """빈 쿼리는 실패"""
    with pytest.raises(ValidationError):
        validate_input("", "context", 0.8, 1.0)
```

**2. Mocking (모의 객체)**
```python
from unittest.mock import Mock, patch

@patch('openai.ChatCompletion.create')
def test_llm_call(mock_create):
    # OpenAI API를 모킹
    mock_create.return_value = Mock(
        choices=[Mock(message=Mock(content="Response"))],
        usage=Mock(prompt_tokens=100, completion_tokens=50)
    )

    client = LLMClient(api_key="test")
    response = client.generate("query", "context")

    assert response.content == "Response"
    assert mock_create.called
```

**3. Fixtures (테스트 데이터)**
```python
import pytest

@pytest.fixture
def sample_optimizer():
    """재사용 가능한 optimizer 객체"""
    return ProductionOptimizer()

@pytest.fixture
def sample_query():
    return "What is context engineering?"

def test_optimization(sample_optimizer, sample_query):
    result = sample_optimizer.optimize(sample_query, "", 0.8)
    assert result['tokens'] > 0
```

### 실습 (15시간)

#### Exercise 8: Unit Tests 작성 (5시간)

**과제**: 모든 핵심 함수에 unit test 작성

```python
# tests/test_optimizer.py

import pytest
from project.resilient_optimizer import ResilientOptimizer

class TestResilientOptimizer:

    @pytest.fixture
    def optimizer(self):
        return ResilientOptimizer()

    def test_optimize_success(self, optimizer):
        """TODO: 정상 케이스 테스트"""
        pass

    def test_optimize_invalid_input(self, optimizer):
        """TODO: 잘못된 입력 테스트"""
        pass

    def test_optimize_retry_on_failure(self, optimizer):
        """TODO: 재시도 로직 테스트"""
        pass

    def test_circuit_breaker_opens(self, optimizer):
        """TODO: Circuit breaker 테스트"""
        pass
```

**목표 커버리지**: 80%+

```bash
pytest tests/test_optimizer.py -v --cov=project --cov-report=html
open htmlcov/index.html
```

#### Exercise 9: Integration Tests (5시간)

**과제**: 실제 API 호출 테스트

```python
# tests/integration/test_llm_integration.py

import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No API key")
class TestLLMIntegration:

    def test_real_openai_call(self):
        """실제 OpenAI API 호출"""
        from examples.production_ready.clients.llm_client import ProductionLLMClient

        client = ProductionLLMClient(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.generate(
            query="What is 2+2?",
            context="You are a math tutor.",
            model="gpt-3.5-turbo",
            max_tokens=10
        )

        assert response.content
        assert response.cost > 0
        assert response.usage['total_tokens'] > 0

    def test_rate_limiting(self):
        """Rate limiting 테스트"""
        # TODO: 빠르게 여러 요청 보내서 rate limit 확인
        pass
```

**실행**:
```bash
# Integration tests만 실행
pytest tests/integration/ -v -m integration

# 전체 테스트
pytest tests/ -v
```

#### Exercise 10: Mocking External Services (3시간)

**과제**: 외부 서비스 모킹

```python
# tests/test_optimizer_with_mocks.py

from unittest.mock import Mock, patch
import pytest

class TestOptimizerWithMocks:

    @patch('tiktoken.get_encoding')
    def test_token_counting_with_mock(self, mock_encoding):
        """tiktoken을 모킹하여 테스트"""

        # Mock 설정
        mock_enc = Mock()
        mock_enc.encode.return_value = [1, 2, 3, 4, 5]
        mock_encoding.return_value = mock_enc

        # 테스트
        from shared.utils import count_tokens
        result = count_tokens("test text")

        assert result == 5
        mock_enc.encode.assert_called_once_with("test text")

    @patch('redis.Redis')
    def test_caching_with_mock_redis(self, mock_redis):
        """Redis를 모킹하여 캐시 테스트"""
        # TODO: 구현
        pass

    @patch('openai.ChatCompletion.create')
    def test_llm_error_handling(self, mock_create):
        """LLM API 오류 처리 테스트"""
        from openai import RateLimitError

        # API가 실패하도록 설정
        mock_create.side_effect = RateLimitError("Rate limit exceeded")

        # TODO: 재시도 로직이 동작하는지 확인
        pass
```

#### Exercise 11: Parametrized Tests (2시간)

**과제**: 여러 입력을 한번에 테스트

```python
# tests/test_validation_parametrized.py

import pytest
from project.resilient_optimizer import validate_optimization_request, ValidationError

@pytest.mark.parametrize("query,context,min_quality,max_cost,should_pass", [
    ("valid", "valid", 0.8, 1.0, True),
    (None, "valid", 0.8, 1.0, False),
    ("", "valid", 0.8, 1.0, False),
    ("valid", "valid", 1.5, 1.0, False),
    ("valid", "valid", 0.8, -1.0, False),
    ("x" * 100000, "valid", 0.8, 1.0, False),  # Too long
])
def test_validate_optimization_request(query, context, min_quality, max_cost, should_pass):
    if should_pass:
        q, c = validate_optimization_request(query, context, min_quality, max_cost)
        assert q and c
    else:
        with pytest.raises(ValidationError):
            validate_optimization_request(query, context, min_quality, max_cost)
```

### 프로젝트 과제 (3시간)

**최종 프로젝트**: "Fully Tested Optimizer"

요구사항:
1. 80%+ 코드 커버리지
2. Unit tests (20개 이상)
3. Integration tests (5개 이상)
4. Mocking 사용
5. Parametrized tests
6. CI에서 자동 실행

```
project/
├── optimizer.py           # 메인 코드
├── tests/
│   ├── unit/
│   │   ├── test_validation.py
│   │   ├── test_retry.py
│   │   ├── test_circuit_breaker.py
│   │   └── test_optimizer.py
│   ├── integration/
│   │   ├── test_llm_integration.py
│   │   └── test_cache_integration.py
│   └── conftest.py        # Shared fixtures
├── pytest.ini
└── .github/
    └── workflows/
        └── test.yml       # CI configuration
```

**검증**:
```bash
# 로컬 테스트
pytest tests/ -v --cov=project --cov-report=html --cov-report=term

# CI 시뮬레이션
pytest tests/ --cov=project --cov-report=xml --cov-fail-under=80
```

## Day 8-10: CI/CD Setup (10시간)

### 학습 목표
코드 변경 시 자동으로 테스트하고 배포합니다.

### 실습 (8시간)

#### Exercise 12: GitHub Actions CI (4시간)

**과제**: CI 파이프라인 구축

```.github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ -v --cov=project --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

#### Exercise 13: Pre-commit Hooks (2시간)

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
```

```bash
# 설치
pip install pre-commit
pre-commit install

# 실행
pre-commit run --all-files
```

### 프로젝트 과제 (2시간)

**최종 프로젝트**: "Complete CI/CD Pipeline"

요구사항:
1. GitHub Actions workflow
2. 테스트 자동 실행
3. 코드 커버리지 리포트
4. Pre-commit hooks
5. Linting (black, flake8, mypy)

## Week 1-2 종합 평가

### 체크리스트

#### Error Handling
- [ ] 모든 함수에 try-except
- [ ] Retry logic 구현
- [ ] Circuit breaker 구현
- [ ] Input validation
- [ ] Custom exceptions

#### Logging
- [ ] JSON 구조화 로깅
- [ ] Request ID 추적
- [ ] 메트릭 로깅
- [ ] 에러 로그 with stack trace
- [ ] Log rotation

#### Testing
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] Mocking external services
- [ ] Parametrized tests
- [ ] CI/CD pipeline

### 최종 프로젝트

**"Production-Ready Context Optimizer v1.0"**

완성해야 할 것:
```python
# optimizer_v1.py

from examples.production_ready.core.error_handling import *
from examples.production_ready.core.logging_config import *

class ProductionContextOptimizer:
    """
    프로덕션 준비 완료된 optimizer

    Features:
    - Error handling with retry
    - Circuit breaker
    - Structured logging
    - Full test coverage
    - CI/CD ready
    """

    def __init__(self, config: Config):
        # Setup logging
        setup_logging(level=config.log_level, json_logs=True)

        # Initialize components
        self.circuit_breaker = CircuitBreaker(...)
        self.logger = RequestLogger(...)
        self.metrics = MetricsLogger(...)

    def optimize(self, query: str, context: str, request_id: str) -> dict:
        """
        Optimize with full error handling and logging
        """
        # Validate
        # Log
        # Process with retry
        # Handle errors
        # Return result
        pass
```

**평가 기준**:
- [ ] 모든 에러를 처리
- [ ] 모든 동작을 로깅
- [ ] 80%+ 테스트 커버리지
- [ ] CI 통과
- [ ] 문서화 완료

### 다음 단계

✅ Week 1-2 완료 시:
- 견고한 에러 핸들링 ✅
- 완전한 관찰성 ✅
- 테스트로 보장된 품질 ✅

📚 **[Week 3-4: Data & Caching으로 →](../week-03-04-data-caching/README.md)**

---

**💡 학습 팁**:
- 에러 핸들링은 처음부터 구현하세요 (나중에 추가하기 어렵습니다)
- 로그는 미래의 당신을 위한 것입니다
- 테스트는 리팩토링의 자신감을 줍니다
- CI/CD는 시간을 절약합니다

**🎯 목표**: 안정적이고 관찰 가능한 시스템!

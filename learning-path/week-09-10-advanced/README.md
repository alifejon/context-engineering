# Week 9-10: Advanced Topics & Optimization

**학습 기간**: 2주 (40시간)
**목표**: 비동기 처리 + 성능 최적화 + 고급 보안 + 대규모 트래픽 대응

## 📋 학습 목표

이 2주 과정을 마치면 다음을 할 수 있습니다:

- ✅ 비동기 I/O로 10배 성능 향상
- ✅ Connection pooling & 캐시 전략
- ✅ 대규모 배치 처리
- ✅ 고급 보안 (OAuth2, RBAC)
- ✅ Circuit breaker & Bulkhead 패턴
- ✅ 분산 추적 (OpenTelemetry)
- ✅ 부하 테스트 & 튜닝
- ✅ Chaos Engineering

## 🎯 필수 선수 지식

- Week 1-8 완료
- Python `asyncio` 기본 이해
- 동기 vs 비동기 차이 이해
- HTTP/2, gRPC 개념 (선택)

## 📚 학습 자료

### 공식 문서
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [httpx Async Client](https://www.python-httpx.org/async/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)

### 추천 아티클
- [FastAPI Async Best Practices](https://github.com/zhanymkanov/fastapi-best-practices#1-async-routes)
- [Python Async Patterns](https://realpython.com/async-io-python/)
- [Microservices Patterns](https://microservices.io/patterns/index.html)

## 📅 2주 학습 계획

```
Week 9 (20시간)
├── Day 1-2: 비동기 I/O & Database (10시간)
│   ├── async/await 패턴
│   ├── AsyncIO event loop
│   ├── Async SQLAlchemy
│   └── Connection pooling
│
└── Day 3-4: 성능 최적화 (10시간)
    ├── Batch processing
    ├── 캐시 전략 (multi-layer)
    ├── Query optimization
    └── 부하 테스트

Week 10 (20시간)
├── Day 1-2: 고급 보안 & Resilience (10시간)
│   ├── OAuth2 with scopes
│   ├── RBAC (Role-Based Access Control)
│   ├── Circuit breaker
│   └── Bulkhead pattern
│
├── Day 3: Observability (5시간)
│   ├── Distributed tracing
│   ├── OpenTelemetry
│   └── Jaeger
│
└── Day 4: Chaos Engineering (5시간)
    ├── Chaos Mesh
    ├── Failure injection
    └── Recovery testing
```

---

## Week 9: 비동기 처리 & 성능 최적화

### Day 1-2: 비동기 I/O & Database (10시간)

#### 📖 이론: 동기 vs 비동기

**동기 처리 (Blocking I/O)**:

```python
# Synchronous (blocking)
def fetch_data():
    response1 = requests.get("https://api1.com")  # Wait 500ms
    response2 = requests.get("https://api2.com")  # Wait 500ms
    response3 = requests.get("https://api3.com")  # Wait 500ms
    return [response1, response2, response3]

# Total time: 1500ms (500 + 500 + 500)
```

**비동기 처리 (Non-blocking I/O)**:

```python
# Asynchronous (non-blocking)
async def fetch_data():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get("https://api1.com"),  # Start all 3
            client.get("https://api2.com"),  # at the same time
            client.get("https://api3.com")
        ]
        responses = await asyncio.gather(*tasks)
    return responses

# Total time: ~500ms (parallel execution)
```

**성능 비교**:

| 작업 타입 | 동기 (req/s) | 비동기 (req/s) | 개선 |
|----------|-------------|---------------|------|
| CPU 집약적 (계산) | 100 | 100 | 1x (차이 없음) |
| I/O 집약적 (API 호출) | 50 | 500 | 10x |
| Mixed | 70 | 300 | 4x |

**언제 비동기를 사용하나?**

✅ **사용해야 할 때**:
- 외부 API 호출 (OpenAI, Pinecone, etc.)
- 데이터베이스 쿼리
- 파일 I/O
- 네트워크 요청

❌ **사용하지 말아야 할 때**:
- CPU 집약적 작업 (이미지 처리, 머신러닝 추론)
- 간단한 CRUD (오버헤드가 더 큼)

#### 💻 실습 1: Async SQLAlchemy (3시간)

**1단계: 의존성 설치**

```bash
pip install sqlalchemy[asyncio] asyncpg  # PostgreSQL async driver
```

**2단계: Async Engine 설정** (`database.py`):

```python
"""
Async database configuration.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import get_settings

settings = get_settings()

# Async engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_size=20,          # Connection pool size
    max_overflow=10,       # Max overflow connections
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Async dependency to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**3단계: Async 모델** (`models/user.py`):

```python
"""
User model (no changes needed for async).
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    # ... rest same as before
```

**4단계: Async 리포지토리 패턴** (`repositories/user_repository.py`):

```python
"""
User repository with async operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import Optional, List
from ..models.user import User
from ..schemas.auth import UserCreate


class UserRepository:
    """Async user repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create new user."""
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        self.db.add(user)
        await self.db.flush()  # Get ID without committing
        await self.db.refresh(user)
        return user

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user."""
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
```

**5단계: Async 라우터** (`routers/auth.py`):

```python
"""
Async auth router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..repositories.user_repository import UserRepository
from ..schemas.auth import UserCreate, UserResponse, Token

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user (async).
    """
    repo = UserRepository(db)

    # Check if user exists (runs in parallel!)
    existing_user, existing_email = await asyncio.gather(
        repo.get_by_username(user_data.username),
        repo.get_by_email(user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password (CPU-intensive, run in thread pool)
    hashed_password = await asyncio.to_thread(
        AuthService.hash_password,
        user_data.password
    )

    # Create user
    user = await repo.create(user_data, hashed_password)

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login (async)."""
    repo = UserRepository(db)

    # Get user
    user = await repo.get_by_username(form_data.username)
    if not user:
        user = await repo.get_by_email(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Verify password (CPU-intensive, run in thread pool)
    password_valid = await asyncio.to_thread(
        AuthService.verify_password,
        form_data.password,
        user.hashed_password
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create token
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }
```

**핵심 패턴**:

1. **`asyncio.gather()`**: 여러 async 작업을 병렬로 실행
   ```python
   user, profile = await asyncio.gather(
       repo.get_user(user_id),
       repo.get_profile(user_id)
   )
   ```

2. **`asyncio.to_thread()`**: CPU 집약적 작업을 thread pool에서 실행
   ```python
   result = await asyncio.to_thread(cpu_intensive_function, data)
   ```

3. **Connection pooling**: `pool_size=20` → 20개 동시 연결 재사용

#### 💻 실습 2: Async LLM Client (3시간)

```python
"""
Async LLM client for high throughput.
"""
import httpx
import asyncio
from typing import List
from openai import AsyncOpenAI

class AsyncLLMClient:
    """Async OpenAI client."""

    def __init__(self, api_key: str, max_concurrent: int = 10):
        self.client = AsyncOpenAI(api_key=api_key)
        self.semaphore = asyncio.Semaphore(max_concurrent)  # Limit concurrency

    async def generate(self, query: str, context: str, model: str) -> dict:
        """
        Generate response (async).
        """
        async with self.semaphore:  # Limit to max_concurrent requests
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": query}
                ]
            )

            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.model_dump()
            }

    async def batch_generate(self, requests: List[dict]) -> List[dict]:
        """
        Batch generate (parallel).

        Args:
            requests: [{"query": "...", "context": "...", "model": "..."}, ...]

        Returns:
            List of responses
        """
        tasks = [
            self.generate(req["query"], req["context"], req["model"])
            for req in requests
        ]

        # Run all in parallel (up to max_concurrent)
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle errors
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append({
                    "error": str(response),
                    "request_index": i
                })
            else:
                results.append(response)

        return results


# Usage
@router.post("/optimize/batch")
async def batch_optimize(
    requests: List[OptimizationRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch optimization (async).

    Process up to 100 requests in parallel.
    """
    if len(requests) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 requests per batch"
        )

    client = AsyncLLMClient(
        api_key=settings.openai_api_key,
        max_concurrent=10  # 10 parallel requests to OpenAI
    )

    # Prepare requests
    llm_requests = [
        {
            "query": req.query,
            "context": req.context,
            "model": req.model
        }
        for req in requests
    ]

    # Execute in parallel
    start_time = time.time()
    responses = await client.batch_generate(llm_requests)
    duration = time.time() - start_time

    logger.info(
        f"Batch optimization completed: {len(requests)} requests in {duration:.2f}s"
    )

    return {
        "responses": responses,
        "total_requests": len(requests),
        "duration_seconds": duration,
        "average_per_request": duration / len(requests)
    }
```

**성능 비교**:

```
동기 처리 (10 requests):
- 각 요청: 2초
- 총 시간: 20초

비동기 처리 (10 requests, max_concurrent=10):
- 각 요청: 2초
- 총 시간: ~2초 (10배 빠름!)
```

---

### Day 3-4: 성능 최적화 (10시간)

#### 📖 이론: 캐시 전략

**Multi-layer Caching**:

```
Request
  ↓
┌─────────────────┐
│ 1. In-Memory    │  (milliseconds)
│    functools.lru_cache
└─────────────────┘
  ↓ Cache miss
┌─────────────────┐
│ 2. Redis        │  (milliseconds)
│    distributed
└─────────────────┘
  ↓ Cache miss
┌─────────────────┐
│ 3. Database     │  (10-100ms)
│    PostgreSQL
└─────────────────┘
  ↓ Cache miss
┌─────────────────┐
│ 4. External API │  (100-1000ms)
│    OpenAI, etc.
└─────────────────┘
```

**캐시 무효화 전략**:

| 전략 | 설명 | 사용 사례 |
|------|------|-----------|
| **TTL** | 시간 기반 만료 | 자주 변하지 않는 데이터 |
| **Write-through** | 쓸 때마다 캐시 업데이트 | 일관성 중요 |
| **Write-behind** | 쓰기를 큐에 넣고 나중에 처리 | 쓰기 성능 중요 |
| **Cache-aside** | 읽을 때만 캐시 (lazy loading) | 읽기 많음 |

#### 💻 실습 3: Multi-layer Cache (4시간)

```python
"""
Multi-layer cache implementation.
"""
import functools
import hashlib
import pickle
from typing import Optional, Any, Callable
from redis.asyncio import Redis
import asyncio

class MultiLayerCache:
    """
    3-layer cache: Memory → Redis → Source
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self._memory_cache = {}  # In-memory cache

    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        # Create deterministic hash
        key_data = f"{prefix}:{sorted(kwargs.items())}"
        hash_key = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (memory → redis).
        """
        # Layer 1: Memory
        if key in self._memory_cache:
            return self._memory_cache[key]

        # Layer 2: Redis
        value = await self.redis.get(key)
        if value:
            # Deserialize
            data = pickle.loads(value)

            # Promote to memory cache
            self._memory_cache[key] = data

            return data

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        memory_ttl: int = 60
    ):
        """
        Set value in cache (both layers).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Redis TTL in seconds
            memory_ttl: Memory TTL in seconds
        """
        # Layer 1: Memory (short TTL)
        self._memory_cache[key] = value

        # Schedule memory eviction
        asyncio.create_task(self._evict_memory(key, memory_ttl))

        # Layer 2: Redis (long TTL)
        serialized = pickle.dumps(value)
        await self.redis.setex(key, ttl, serialized)

    async def _evict_memory(self, key: str, ttl: int):
        """Evict key from memory after TTL."""
        await asyncio.sleep(ttl)
        self._memory_cache.pop(key, None)

    async def delete(self, key: str):
        """Delete from all layers."""
        self._memory_cache.pop(key, None)
        await self.redis.delete(key)

    def cached(
        self,
        prefix: str,
        ttl: int = 3600,
        key_builder: Optional[Callable] = None
    ):
        """
        Decorator for caching function results.

        Usage:
            @cache.cached(prefix="user", ttl=3600)
            async def get_user(user_id: int):
                return await db.get(user_id)
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._generate_key(prefix, args=args, kwargs=kwargs)

                # Try cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Cache miss - call function
                result = await func(*args, **kwargs)

                # Store in cache
                await self.set(cache_key, result, ttl=ttl)

                return result

            return wrapper
        return decorator


# Usage example
cache = MultiLayerCache(redis_client)

@cache.cached(prefix="optimization", ttl=3600)
async def get_optimization_result(query: str, context: str, model: str):
    """
    Cached optimization.

    Same query+context+model → return cached result
    """
    # Expensive operation
    result = await optimization_service.optimize(query, context, model)
    return result


# Manual cache usage
async def get_user_profile(user_id: int):
    cache_key = f"user_profile:{user_id}"

    # Try cache
    profile = await cache.get(cache_key)
    if profile:
        return profile

    # Cache miss
    profile = await db.query(UserProfile).filter_by(user_id=user_id).first()

    # Store in cache
    await cache.set(cache_key, profile, ttl=1800)  # 30 minutes

    return profile
```

#### ✍️ Exercise 1: Query Optimization (2시간)

**목표**: N+1 쿼리 문제 해결

**문제 코드**:

```python
# ❌ Bad: N+1 queries
async def get_users_with_profiles(db: AsyncSession):
    """
    Gets 100 users + profiles.

    Queries:
    1. SELECT * FROM users LIMIT 100  (1 query)
    2-101. SELECT * FROM profiles WHERE user_id = ?  (100 queries)

    Total: 101 queries!
    ```
    users = await db.execute(select(User).limit(100))
    users = users.scalars().all()

    # N+1 problem!
    for user in users:
        user.profile = await db.execute(
            select(Profile).where(Profile.user_id == user.id)
        )

    return users
```

**TODO: 최적화**

```python
# ✅ Good: Eager loading with joinedload
from sqlalchemy.orm import joinedload

async def get_users_with_profiles_optimized(db: AsyncSession):
    """
    TODO: joinedload를 사용하여 1개의 쿼리로 해결

    힌트:
    result = await db.execute(
        select(User).options(joinedload(User.profile)).limit(100)
    )
    ```
    # TODO: 구현
    pass
```

---

## Week 10: 고급 보안 & Resilience

### Day 1-2: Circuit Breaker & Bulkhead (10시간)

#### 📖 이론: Resilience Patterns

**1. Circuit Breaker**:

```
CLOSED (정상)
    ↓ (failures > threshold)
OPEN (차단)
    ↓ (timeout)
HALF_OPEN (테스트)
    ↓ (success)
CLOSED
```

**2. Bulkhead (격벽)**:

```
Request Pool (분리)
├── OpenAI API: 10 concurrent max
├── Database: 20 concurrent max
└── Redis: 50 concurrent max

→ 하나가 느려져도 다른 것에 영향 없음
```

#### 💻 실습 4: Circuit Breaker 구현 (3시간)

```python
"""
Circuit breaker for external services.
"""
from enum import Enum
from datetime import datetime, timedelta
import asyncio
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Blocking calls
    HALF_OPEN = "half_open"  # Testing


class AsyncCircuitBreaker:
    """
    Async circuit breaker.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        """
        async with self._lock:
            # Check if circuit should transition to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception(
                        f"Circuit breaker is OPEN. "
                        f"Retry after {self._time_until_retry():.0f}s"
                    )

        # Call function
        try:
            result = await func(*args, **kwargs)

            # Success
            async with self._lock:
                await self._on_success()

            return result

        except self.expected_exception as e:
            # Failure
            async with self._lock:
                await self._on_failure()

            raise

    async def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                # Enough successes → close circuit
                self.state = CircuitState.CLOSED
                self.success_count = 0

    async def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed in HALF_OPEN → reopen circuit
            self.state = CircuitState.OPEN
            self.success_count = 0

        elif self.failure_count >= self.failure_threshold:
            # Too many failures → open circuit
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try HALF_OPEN."""
        if not self.last_failure_time:
            return True

        return (datetime.now() - self.last_failure_time).total_seconds() >= self.timeout

    def _time_until_retry(self) -> float:
        """Time until retry is allowed."""
        if not self.last_failure_time:
            return 0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, self.timeout - elapsed)


# Usage
openai_breaker = AsyncCircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    expected_exception=OpenAIError
)

async def call_openai(query: str):
    """Call OpenAI with circuit breaker."""
    return await openai_breaker.call(
        client.chat.completions.create,
        model="gpt-4",
        messages=[{"role": "user", "content": query}]
    )
```

#### ✍️ Exercise 2: Distributed Rate Limiter (3시간)

**목표**: Redis 기반 분산 rate limiter

```python
"""
Distributed rate limiter using Redis.
"""
from redis.asyncio import Redis
import time

class DistributedRateLimiter:
    """
    TODO: Sliding window rate limiter with Redis

    요구사항:
    1. Redis sorted set 사용
    2. Sliding window 알고리즘
    3. 분산 환경에서 동작 (여러 서버)
    """

    def __init__(self, redis: Redis, max_requests: int, window_seconds: int):
        self.redis = redis
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """
        TODO: Check if request is allowed

        Algorithm:
        1. Current timestamp
        2. Remove old entries (older than window)
        3. Count entries in window
        4. If count < max_requests:
               Add current timestamp
               Return True
           Else:
               Return False

        Hint: Redis commands
        - ZREMRANGEBYSCORE (remove old)
        - ZCARD (count)
        - ZADD (add)
        - EXPIRE (set TTL)
        ```
        pass

    async def get_remaining(self, key: str) -> int:
        """TODO: Get remaining requests in current window"""
        pass
```

---

### Day 3: Distributed Tracing (5시간)

#### 💻 실습 5: OpenTelemetry 통합 (5시간)

```python
"""
OpenTelemetry instrumentation.
"""
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Setup tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument SQLAlchemy
SQLAlchemyInstrumentor().instrument(engine=engine)

# Auto-instrument Redis
RedisInstrumentor().instrument()


# Manual instrumentation
@router.post("/optimize")
async def optimize_context(...):
    # Create custom span
    with tracer.start_as_current_span("optimization") as span:
        span.set_attribute("user_id", current_user.id)
        span.set_attribute("strategy", request.strategy)

        # Child span
        with tracer.start_as_current_span("compress"):
            compressed = await compress_context(request.context)

        with tracer.start_as_current_span("llm_call"):
            result = await llm_client.generate(...)

        return result
```

---

### Day 4: Chaos Engineering (5시간)

#### 💻 실습 6: 장애 주입 테스트 (5시간)

```python
"""
Chaos testing utilities.
"""
import random
import asyncio

class ChaosMiddleware:
    """
    Inject failures for testing resilience.

    WARNING: Only use in test/staging!
    """

    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate

    async def __call__(self, request: Request, call_next):
        # Random delay (latency injection)
        if random.random() < self.failure_rate:
            delay = random.uniform(1, 5)
            await asyncio.sleep(delay)

        # Random error (error injection)
        if random.random() < self.failure_rate / 2:
            raise HTTPException(
                status_code=500,
                detail="Chaos monkey strikes!"
            )

        return await call_next(request)


# Add to app (ONLY in staging!)
if settings.environment == "staging":
    app.add_middleware(ChaosMiddleware, failure_rate=0.1)
```

---

## ✅ Week 9-10 체크리스트

### 비동기 처리
- [ ] Async SQLAlchemy 구현
- [ ] Async LLM client
- [ ] Batch processing
- [ ] Connection pooling

### 성능 최적화
- [ ] Multi-layer caching
- [ ] Query optimization (N+1 해결)
- [ ] 부하 테스트 (k6/Locust)
- [ ] 프로파일링

### Resilience
- [ ] Circuit breaker 구현
- [ ] Bulkhead pattern
- [ ] Retry with backoff
- [ ] Graceful degradation

### Observability
- [ ] OpenTelemetry 통합
- [ ] Distributed tracing
- [ ] Jaeger 대시보드
- [ ] Custom spans

### 보안
- [ ] OAuth2 with scopes
- [ ] RBAC 구현
- [ ] API key rotation
- [ ] Security headers

---

## 🎓 최종 프로젝트

완료 기준:
- [ ] 비동기 API (처리량 > 1000 req/s)
- [ ] Multi-layer cache (히트율 > 60%)
- [ ] Circuit breaker 동작 확인
- [ ] Distributed tracing 설정
- [ ] 부하 테스트 통과 (P95 < 500ms)
- [ ] Chaos testing 통과

**다음**: Final Project로 이동하여 통합 시스템 구축!

# Week 5-6: API Server & Authentication

**학습 기간**: 2주 (40시간)
**목표**: FastAPI로 프로덕션급 API 서버 구축 + JWT 인증 + Rate Limiting

## 📋 학습 목표

이 2주 과정을 마치면 다음을 할 수 있습니다:

- ✅ FastAPI로 RESTful API 서버 구축
- ✅ JWT 기반 인증/인가 시스템 구현
- ✅ Rate limiting으로 API 보호
- ✅ Pydantic으로 입력 검증
- ✅ OpenAPI/Swagger 문서 자동 생성
- ✅ 미들웨어로 로깅/에러 처리
- ✅ 비동기 처리로 성능 최적화
- ✅ API 버저닝 전략 구현

## 🎯 필수 선수 지식

- Week 1-2 완료 (Error handling, Logging, Testing)
- Week 3-4 완료 (PostgreSQL, Redis, SQLAlchemy)
- Python 비동기 프로그래밍 기초 (`async`/`await`)
- HTTP/REST API 기본 개념
- JWT 토큰 개념

## 📚 학습 자료

### 공식 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Pydantic v2 문서](https://docs.pydantic.dev/latest/)
- [python-jose JWT 문서](https://python-jose.readthedocs.io/)
- [slowapi 문서](https://github.com/laurentS/slowapi)

### 추천 아티클
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [JWT Authentication Tutorial](https://testdriven.io/blog/fastapi-jwt-auth/)
- [Rate Limiting Strategies](https://www.nginx.com/blog/rate-limiting-nginx/)

## 📅 2주 학습 계획

```
Week 5 (20시간)
├── Day 1-2: FastAPI 기초 & 프로젝트 구조 (12시간)
│   ├── FastAPI 앱 구조 설계
│   ├── Pydantic 모델 정의
│   ├── CRUD API 구현
│   └── OpenAPI 문서 커스터마이징
│
├── Day 3-4: JWT 인증 시스템 (8시간)
    ├── 사용자 모델 & 비밀번호 해싱
    ├── JWT 토큰 발급/검증
    ├── 로그인/회원가입 API
    └── 인증 의존성 구현

Week 6 (20시간)
├── Day 1-2: Rate Limiting & 보안 (8시간)
│   ├── Rate limiter 구현
│   ├── CORS 설정
│   ├── API 키 인증
│   └── 보안 헤더 추가
│
├── Day 3: 미들웨어 & 에러 처리 (6시간)
│   ├── 로깅 미들웨어
│   ├── 에러 핸들러
│   └── Request ID 추적
│
└── Day 4: 통합 테스트 & 배포 준비 (6시간)
    ├── pytest + TestClient
    ├── 인증 테스트
    └── Docker 이미지 빌드
```

---

## Week 5: FastAPI 기초 & JWT 인증

### Day 1-2: FastAPI 기초 & 프로젝트 구조 (12시간)

#### 🎯 학습 목표
- FastAPI 앱의 올바른 프로젝트 구조 이해
- Pydantic 모델로 요청/응답 검증
- CRUD API 엔드포인트 구현
- 의존성 주입(Dependency Injection) 활용

#### 📖 이론: FastAPI 프로젝트 구조

**프로덕션 레벨 구조**:
```
api/
├── __init__.py
├── main.py                 # FastAPI 앱 진입점
├── config.py               # 설정 관리
├── dependencies.py         # 공통 의존성
│
├── models/                 # SQLAlchemy 모델
│   ├── __init__.py
│   ├── user.py
│   └── optimization.py
│
├── schemas/                # Pydantic 스키마
│   ├── __init__.py
│   ├── user.py
│   ├── optimization.py
│   └── common.py
│
├── routers/                # API 라우터
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   └── optimize.py
│
├── services/               # 비즈니스 로직
│   ├── __init__.py
│   ├── auth_service.py
│   └── optimization_service.py
│
└── middleware/             # 미들웨어
    ├── __init__.py
    ├── logging.py
    └── error_handler.py
```

**왜 이런 구조인가?**

1. **models/** vs **schemas/**:
   - `models/`: 데이터베이스 테이블 정의 (SQLAlchemy ORM)
   - `schemas/`: API 요청/응답 형식 (Pydantic)
   - 분리 이유: DB 구조와 API 인터페이스는 독립적으로 변경 가능해야 함

2. **routers/** vs **services/**:
   - `routers/`: HTTP 요청 처리 (라우팅, 검증, 응답)
   - `services/`: 비즈니스 로직 (알고리즘, 계산, DB 접근)
   - 분리 이유: 로직 재사용, 테스트 용이성

3. **dependencies.py**:
   - 공통 의존성 함수 (DB 세션, 현재 사용자, 설정 등)
   - FastAPI의 DI 시스템 활용

#### 💻 실습 1: FastAPI 앱 기본 구조 (3시간)

**1단계: 프로젝트 설정**

```bash
# 디렉토리 생성
mkdir -p api/{models,schemas,routers,services,middleware}
cd api

# 의존성 설치
pip install fastapi uvicorn[standard] pydantic pydantic-settings
```

**2단계: 설정 관리 (`config.py`)**

```python
"""
Configuration management using Pydantic Settings.
환경변수 + .env 파일을 자동으로 읽음
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "Context Optimization API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:pass@localhost/contextdb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str

    # JWT
    secret_key: str  # openssl rand -hex 32
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    @lru_cache ensures only one Settings object is created.
    """
    return Settings()


# Example .env file:
"""
# .env
APP_NAME="Context Optimization API"
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost/contextdb
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3000", "https://app.example.com"]
"""
```

**핵심 개념**:
- `BaseSettings`는 환경변수를 자동으로 읽어서 타입 변환
- `@lru_cache()`로 싱글톤 패턴 구현
- 타입 힌트로 검증 자동화

**3단계: Pydantic 스키마 정의 (`schemas/optimization.py`)**

```python
"""
Pydantic schemas for optimization API.

Request/Response 모델 정의
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class OptimizationRequest(BaseModel):
    """Request body for optimization endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User query",
        examples=["What is context engineering?"]
    )

    context: str = Field(
        default="",
        max_length=500000,
        description="Context to optimize"
    )

    model: str = Field(
        default="gpt-4-turbo",
        description="Target LLM model",
        pattern="^gpt-(3\\.5|4)(-turbo)?$"
    )

    max_tokens: int = Field(
        default=4000,
        ge=1000,
        le=100000,
        description="Maximum context tokens"
    )

    strategy: str = Field(
        default="hybrid",
        description="Optimization strategy",
        pattern="^(truncate|compress|hybrid)$"
    )

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not empty/whitespace."""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class OptimizationMetrics(BaseModel):
    """Optimization metrics."""

    original_tokens: int
    optimized_tokens: int
    reduction_ratio: float
    estimated_cost_before: float
    estimated_cost_after: float
    cost_savings: float
    processing_time_ms: float


class OptimizationResponse(BaseModel):
    """Response body for optimization endpoint."""

    request_id: str = Field(..., description="Unique request ID")
    optimized_context: str = Field(..., description="Optimized context")
    metrics: OptimizationMetrics
    strategy_used: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req_abc123",
                    "optimized_context": "Context engineering is...",
                    "metrics": {
                        "original_tokens": 5000,
                        "optimized_tokens": 2000,
                        "reduction_ratio": 0.6,
                        "estimated_cost_before": 0.05,
                        "estimated_cost_after": 0.02,
                        "cost_savings": 0.03,
                        "processing_time_ms": 234.5
                    },
                    "strategy_used": "hybrid",
                    "timestamp": "2025-11-08T10:30:00Z"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID if available")
```

**Pydantic 핵심 기능**:
- `Field(...)`: 필수 필드, `Field(default=...)`: 선택 필드
- `min_length`, `max_length`: 문자열 길이 검증
- `ge`, `le`: 숫자 범위 검증 (greater or equal, less or equal)
- `pattern`: 정규식 검증
- `@field_validator`: 커스텀 검증 로직
- `json_schema_extra`: OpenAPI 문서에 예시 추가

**4단계: 라우터 구현 (`routers/optimize.py`)**

```python
"""
Optimization API router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import time
from uuid import uuid4

from ..schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationMetrics,
    ErrorResponse
)
from ..dependencies import get_db, get_current_user
from ..services.optimization_service import OptimizationService
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/optimize",
    tags=["optimization"],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)


@router.post(
    "/",
    response_model=OptimizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimize context",
    description="Optimize context for LLM using specified strategy"
)
async def optimize_context(
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimize context for efficient LLM usage.

    **Strategies**:
    - `truncate`: Simple token-based truncation
    - `compress`: Semantic compression
    - `hybrid`: Deduplication + summarization

    **Example**:
    ```json
    {
        "query": "What is context engineering?",
        "context": "Long context here...",
        "model": "gpt-4-turbo",
        "max_tokens": 4000,
        "strategy": "hybrid"
    }
    ```
    """
    request_id = str(uuid4())
    start_time = time.time()

    logger.info(
        "Optimization request received",
        extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "strategy": request.strategy,
            "query_length": len(request.query),
            "context_length": len(request.context)
        }
    )

    try:
        # Initialize service
        service = OptimizationService(db)

        # Perform optimization
        result = await service.optimize(
            query=request.query,
            context=request.context,
            model=request.model,
            max_tokens=request.max_tokens,
            strategy=request.strategy,
            user_id=current_user.id
        )

        # Calculate metrics
        processing_time_ms = (time.time() - start_time) * 1000

        metrics = OptimizationMetrics(
            original_tokens=result['original_tokens'],
            optimized_tokens=result['optimized_tokens'],
            reduction_ratio=result['reduction_ratio'],
            estimated_cost_before=result['cost_before'],
            estimated_cost_after=result['cost_after'],
            cost_savings=result['cost_savings'],
            processing_time_ms=processing_time_ms
        )

        logger.info(
            "Optimization completed",
            extra={
                "request_id": request_id,
                "metrics": metrics.model_dump(),
                "processing_time_ms": processing_time_ms
            }
        )

        return OptimizationResponse(
            request_id=request_id,
            optimized_context=result['optimized_context'],
            metrics=metrics,
            strategy_used=request.strategy
        )

    except ValueError as e:
        logger.error(
            "Validation error",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.exception(
            "Optimization failed",
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/history",
    response_model=list[OptimizationResponse],
    summary="Get optimization history",
    description="Get user's optimization history"
)
async def get_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get optimization history for current user."""
    service = OptimizationService(db)
    history = await service.get_user_history(current_user.id, limit=limit)
    return history
```

**FastAPI 핵심 패턴**:

1. **의존성 주입 (`Depends`)**:
   ```python
   async def endpoint(
       db: Session = Depends(get_db),
       user: User = Depends(get_current_user)
   ):
   ```
   - FastAPI가 자동으로 `get_db()`, `get_current_user()` 호출
   - 재사용 가능, 테스트 시 mock 가능

2. **자동 검증**:
   - `request: OptimizationRequest` → Pydantic이 자동 검증
   - 실패 시 422 Unprocessable Entity 자동 반환

3. **OpenAPI 문서**:
   - `summary`, `description`: API 설명
   - `response_model`: 응답 형식 정의
   - `responses`: 에러 응답 정의

**5단계: 메인 앱 (`main.py`)**

```python
"""
FastAPI application entrypoint.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from .config import get_settings
from .routers import optimize, auth, users
from .middleware.logging import LoggingMiddleware
from .database import engine, Base

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: startup and shutdown.
    """
    # Startup
    logger.info("Starting application", extra={"app_name": settings.app_name})

    # Create database tables
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready Context Optimization API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware
app.add_middleware(LoggingMiddleware)


# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["authentication"]
)
app.include_router(
    users.router,
    prefix=f"{settings.api_v1_prefix}/users",
    tags=["users"]
)
app.include_router(
    optimize.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["optimization"]
)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """API root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception("Unhandled exception", extra={"path": request.url.path})

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
```

**주요 구성 요소**:

1. **Lifespan events**:
   - Startup: DB 초기화, 연결 풀 생성
   - Shutdown: 리소스 정리

2. **Middleware**:
   - CORS: 브라우저에서 API 호출 허용
   - Logging: 모든 요청 로깅

3. **Router 등록**:
   - `include_router()`로 모듈식 라우터 추가
   - Prefix로 버저닝 (`/api/v1`)

4. **Exception handling**:
   - 전역 에러 핸들러로 모든 예외 처리

#### ✍️ Exercise 1: CRUD API 구현 (3시간)

**목표**: 사용자의 최적화 프로필 CRUD API 구현

**요구사항**:

1. **모델 정의** (`schemas/profile.py`):
```python
from pydantic import BaseModel, Field

class ProfileCreate(BaseModel):
    """TODO: 프로필 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100)
    default_model: str = Field(default="gpt-4-turbo")
    default_strategy: str = Field(default="hybrid")
    max_monthly_cost: float = Field(default=100.0, ge=0)

class ProfileUpdate(BaseModel):
    """TODO: 프로필 수정 요청 (모든 필드 선택적)"""
    # Hint: Optional[] 사용

class ProfileResponse(BaseModel):
    """TODO: 프로필 응답"""
    id: int
    user_id: int
    name: str
    default_model: str
    default_strategy: str
    max_monthly_cost: float
    created_at: datetime
    updated_at: datetime
```

2. **라우터 구현** (`routers/profiles.py`):
```python
router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("/", response_model=ProfileResponse)
async def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """TODO: 프로필 생성"""
    pass

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, ...):
    """TODO: 프로필 조회"""
    pass

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: int, profile: ProfileUpdate, ...):
    """TODO: 프로필 수정"""
    pass

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: int, ...):
    """TODO: 프로필 삭제"""
    pass

@router.get("/", response_model=list[ProfileResponse])
async def list_profiles(...):
    """TODO: 사용자의 모든 프로필 조회"""
    pass
```

3. **테스트 작성** (`tests/test_profiles.py`):
```python
from fastapi.testclient import TestClient

def test_create_profile(client: TestClient, auth_headers):
    """TODO: 프로필 생성 테스트"""
    response = client.post(
        "/api/v1/profiles",
        json={"name": "My Profile", "default_model": "gpt-4"},
        headers=auth_headers
    )
    assert response.status_code == 200
    # ... more assertions

def test_update_profile(client: TestClient, auth_headers):
    """TODO: 프로필 수정 테스트"""
    pass
```

**평가 기준**:
- [ ] 모든 CRUD 엔드포인트 구현 (30점)
- [ ] Pydantic 검증 올바르게 사용 (20점)
- [ ] 에러 처리 (404, 403, 400) (20점)
- [ ] 테스트 커버리지 > 80% (20점)
- [ ] OpenAPI 문서가 명확함 (10점)

**힌트**:
- `ProfileUpdate`는 모든 필드를 `Optional`로
- 프로필 소유자만 수정/삭제 가능하도록 검증
- 존재하지 않는 profile_id → 404
- 다른 사용자의 프로필 접근 → 403

---

### Day 3-4: JWT 인증 시스템 (8시간)

#### 🎯 학습 목표
- JWT 토큰 생성/검증 구현
- 비밀번호 해싱 (bcrypt)
- 로그인/회원가입 API
- 인증이 필요한 엔드포인트 보호

#### 📖 이론: JWT (JSON Web Token)

**JWT 구조**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

Header.Payload.Signature
```

1. **Header**: 알고리즘, 토큰 타입
   ```json
   {"alg": "HS256", "typ": "JWT"}
   ```

2. **Payload**: 사용자 정보 (claims)
   ```json
   {
     "sub": "user_123",  // subject (user ID)
     "exp": 1699999999,  // expiration time
     "iat": 1699900000   // issued at
   }
   ```

3. **Signature**: Header + Payload를 secret key로 서명
   ```python
   HMACSHA256(
     base64UrlEncode(header) + "." + base64UrlEncode(payload),
     secret_key
   )
   ```

**왜 JWT를 사용하나?**

| 세션 기반 인증 | JWT 기반 인증 |
|---------------|--------------|
| 서버에 세션 저장 (메모리/Redis) | 서버에 상태 저장 불필요 (stateless) |
| 세션 DB 조회 필요 | 토큰만 검증하면 됨 |
| 수평 확장 어려움 | 수평 확장 쉬움 |
| 세션 만료 관리 필요 | 토큰 자체에 만료 시간 포함 |

**JWT의 단점**:
- 토큰 취소 어려움 (블랙리스트 필요)
- Payload 크기 제한
- Secret key 유출 시 모든 토큰 무효화

#### 💻 실습 2: JWT 인증 구현 (4시간)

**1단계: 사용자 모델 (`models/user.py`)**

```python
"""
User model for authentication.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.username}>"
```

**2단계: 인증 스키마 (`schemas/auth.py`)**

```python
"""
Authentication schemas.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Username must be alphanumeric."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None
    user_id: Optional[int] = None


class UserResponse(BaseModel):
    """User response (without password)."""

    id: int
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

**3단계: 인증 서비스 (`services/auth_service.py`)**

```python
"""
Authentication service.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User
from ..schemas.auth import UserCreate, TokenData
from ..config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Payload data (must include 'sub' claim)
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> TokenData:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData with user info

        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )

            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return TokenData(username=username, user_id=user_id)

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password.

        Returns:
            User object if authenticated, None otherwise
        """
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Create new user.

        Raises:
            HTTPException: If username/email already exists
        """
        # Check if username exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        hashed_password = AuthService.hash_password(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
```

**핵심 함수**:

1. **`hash_password()`**: bcrypt로 비밀번호 해싱
   ```python
   # "mypassword" → "$2b$12$KIX..."
   ```

2. **`verify_password()`**: 입력 비밀번호 검증
   ```python
   verify_password("mypassword", "$2b$12$KIX...") → True
   ```

3. **`create_access_token()`**: JWT 토큰 생성
   ```python
   token = create_access_token(
       data={"sub": "john", "user_id": 123},
       expires_delta=timedelta(minutes=30)
   )
   ```

4. **`decode_access_token()`**: JWT 토큰 검증 및 파싱
   ```python
   token_data = decode_access_token(token)
   # token_data.username == "john"
   # token_data.user_id == 123
   ```

**4단계: 인증 라우터 (`routers/auth.py`)**

```python
"""
Authentication router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..schemas.auth import UserCreate, UserLogin, Token, UserResponse
from ..services.auth_service import AuthService
from ..dependencies import get_db
from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    **Password requirements**:
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains at least one digit
    """
    logger.info(f"Registration attempt for username: {user_data.username}")

    try:
        user = AuthService.create_user(db, user_data)

        logger.info(f"User registered successfully: {user.username}")

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Login"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.

    Returns JWT access token.
    """
    logger.info(f"Login attempt for username: {form_data.username}")

    # Authenticate user
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        logger.warning(f"Failed login attempt: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in successfully: {user.username}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user"
)
async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information."""
    from ..dependencies import get_current_user
    user = await get_current_user(token, db)
    return user
```

**5단계: 의존성 함수 (`dependencies.py`)**

```python
"""
Common dependencies.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Generator

from .database import SessionLocal
from .models.user import User
from .services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    # Decode token
    token_data = AuthService.decode_access_token(token)

    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are a superuser.

    Raises:
        HTTPException 403: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user
```

**의존성 체인**:
```python
get_current_user
  └→ oauth2_scheme (토큰 추출)
  └→ get_db (DB 세션)
  └→ AuthService.decode_access_token (토큰 검증)
  └→ User 조회

get_current_active_superuser
  └→ get_current_user
  └→ is_superuser 검증
```

#### ✍️ Exercise 2: 인증 테스트 작성 (2시간)

**목표**: 인증 시스템의 모든 경로 테스트

```python
"""
tests/test_auth.py
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base
from api.main import app
from api.dependencies import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client with test database."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_register_user(client):
    """TODO: 회원가입 성공 테스트"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "hashed_password" not in data  # 비밀번호는 응답에 없어야 함


def test_register_duplicate_username(client):
    """TODO: 중복 사용자명으로 회원가입 실패 테스트"""
    # 첫 번째 사용자 생성
    client.post("/api/v1/auth/register", json={...})

    # 같은 사용자명으로 두 번째 시도
    response = client.post("/api/v1/auth/register", json={...})

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_weak_password(client):
    """TODO: 약한 비밀번호로 회원가입 실패 테스트"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak"  # 너무 짧음
        }
    )

    assert response.status_code == 422  # Validation error


def test_login_success(client):
    """TODO: 로그인 성공 테스트"""
    # 사용자 생성
    client.post("/api/v1/auth/register", json={...})

    # 로그인
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "TestPass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_wrong_password(client):
    """TODO: 잘못된 비밀번호로 로그인 실패 테스트"""
    client.post("/api/v1/auth/register", json={...})

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "WrongPass123"}
    )

    assert response.status_code == 401


def test_access_protected_endpoint_without_token(client):
    """TODO: 토큰 없이 보호된 엔드포인트 접근 테스트"""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_access_protected_endpoint_with_token(client):
    """TODO: 토큰으로 보호된 엔드포인트 접근 테스트"""
    # 사용자 생성 및 로그인
    client.post("/api/v1/auth/register", json={...})
    login_response = client.post("/api/v1/auth/login", data={...})
    token = login_response.json()["access_token"]

    # 보호된 엔드포인트 접근
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_token_expiration(client):
    """TODO: 만료된 토큰 테스트"""
    # Hint: AuthService.create_access_token()에 expires_delta=-1 사용
    pass
```

**평가 기준**:
- [ ] 모든 테스트 통과 (40점)
- [ ] Edge cases 커버 (30점)
- [ ] Fixture 올바르게 사용 (20점)
- [ ] 테스트 격리 (각 테스트 독립적) (10점)

---

## Week 6: Rate Limiting & 프로덕션 준비

### Day 1-2: Rate Limiting & 보안 (8시간)

#### 🎯 학습 목표
- Rate limiting으로 API 남용 방지
- CORS 설정
- API 키 기반 인증
- 보안 헤더 추가

#### 📖 이론: Rate Limiting

**왜 Rate Limiting이 필요한가?**

1. **비용 절감**:
   - LLM API 비용은 사용량에 비례
   - 악의적 사용자가 무한정 요청 → 비용 폭탄

2. **서버 보호**:
   - DDoS 공격 방어
   - 리소스 고갈 방지

3. **공정한 사용**:
   - 한 사용자가 모든 리소스 독점 방지

**Rate Limiting 알고리즘**:

| 알고리즘 | 설명 | 장점 | 단점 |
|---------|------|------|------|
| **Fixed Window** | 시간 창(예: 1분)당 N개 요청 허용 | 구현 간단 | 경계에서 burst 가능 |
| **Sliding Window** | 이동하는 시간 창 사용 | Burst 방지 | 메모리 사용량 높음 |
| **Token Bucket** | 토큰이 차오르고, 요청마다 소비 | Burst 허용, 유연함 | 구현 복잡 |
| **Leaky Bucket** | 요청을 큐에 넣고 일정 속도로 처리 | 트래픽 smoothing | 응답 지연 가능 |

**프로덕션 권장**: **Sliding Window** (Redis 사용)

#### 💻 실습 3: Rate Limiting 구현 (4시간)

**1단계: slowapi 설치**

```bash
pip install slowapi
```

**2단계: Rate Limiter 설정 (`middleware/rate_limit.py`)**

```python
"""
Rate limiting middleware using slowapi.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


def get_user_id_or_ip(request: Request) -> str:
    """
    Get rate limit key: user ID if authenticated, else IP address.

    This allows:
    - Authenticated users: rate limit per user
    - Anonymous users: rate limit per IP
    """
    # Try to get user from request state (set by auth dependency)
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter
limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["60/minute"],  # Default: 60 requests per minute
    storage_uri="redis://localhost:6379/1",  # Use Redis for distributed rate limiting
    strategy="moving-window",  # Sliding window algorithm
    headers_enabled=True  # Add rate limit headers to response
)


# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded.

    Returns 429 with retry-after header.
    """
    logger.warning(
        "Rate limit exceeded",
        extra={
            "path": request.url.path,
            "limit": exc.detail,
            "key": get_user_id_or_ip(request)
        }
    )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. {exc.detail}",
            "retry_after": exc.headers.get("Retry-After", "60")
        },
        headers=exc.headers
    )
```

**3단계: Rate Limiter 적용 (`main.py`)**

```python
from .middleware.rate_limit import limiter, custom_rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
```

**4단계: 엔드포인트에 Rate Limit 적용**

```python
from slowapi import Limiter
from fastapi import Request

# Get limiter from app state
limiter = Limiter(...)


@router.post("/optimize")
@limiter.limit("10/minute")  # Override default: 10 requests per minute
async def optimize_context(
    request: Request,  # Required for limiter
    optimization_request: OptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Optimize context (rate limited to 10/minute)."""
    # ... implementation


@router.get("/history")
@limiter.limit("30/minute")  # Less expensive endpoint: 30/minute
async def get_history(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get history (rate limited to 30/minute)."""
    # ... implementation


@router.post("/optimize/batch")
@limiter.limit("2/minute")  # Expensive batch operation: 2/minute
async def batch_optimize(
    request: Request,
    requests: list[OptimizationRequest],
    current_user: User = Depends(get_current_user)
):
    """Batch optimize (rate limited to 2/minute)."""
    # ... implementation
```

**Rate Limit Response Headers**:
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699999999

# When exceeded:
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699999999
```

#### 💻 실습 4: CORS & 보안 헤더 (2시간)

**CORS (Cross-Origin Resource Sharing)**:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "https://app.example.com"  # Production frontend
    ],
    allow_credentials=True,  # Allow cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allowed HTTP methods
    allow_headers=["*"],  # Allowed headers
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],  # Expose custom headers
    max_age=600  # Cache preflight requests for 10 minutes
)
```

**보안 헤더 미들웨어** (`middleware/security.py`):

```python
"""
Security headers middleware.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent XSS attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTPS enforcement (in production)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


# Add to app
app.add_middleware(SecurityHeadersMiddleware)
```

#### ✍️ Exercise 3: API 키 인증 구현 (2시간)

**목표**: JWT 외에 API 키로도 인증 가능하도록 구현

**요구사항**:

1. **API Key 모델** (`models/api_key.py`):
```python
class APIKey(Base):
    """TODO: API Key 모델 정의"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)  # "sk_live_..."
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)  # "Production API", "Development"
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="api_keys")
```

2. **API Key 생성 함수**:
```python
import secrets

def generate_api_key() -> str:
    """TODO: API 키 생성 (예: sk_live_abc123...)"""
    prefix = "sk_live_"
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"
```

3. **API Key 인증 의존성**:
```python
from fastapi import Header, HTTPException

async def get_user_from_api_key(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    TODO: API 키로 사용자 인증

    요구사항:
    - X-API-Key 헤더에서 키 추출
    - DB에서 키 조회
    - is_active 확인
    - last_used_at 업데이트
    - User 반환
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # TODO: 구현
```

4. **JWT 또는 API Key 인증**:
```python
async def get_current_user_flexible(
    jwt_user: User = Depends(get_current_user, use_cache=False),
    api_key_user: User = Depends(get_user_from_api_key, use_cache=False)
) -> User:
    """
    TODO: JWT 또는 API Key 둘 다 허용

    우선순위:
    1. JWT 토큰 (Authorization: Bearer ...)
    2. API Key (X-API-Key: sk_live_...)
    """
    # TODO: 구현
```

5. **API Key 관리 엔드포인트**:
```python
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """TODO: API 키 생성"""
    pass

@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """TODO: 사용자의 API 키 목록"""
    pass

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: int, current_user: User = Depends(get_current_user)):
    """TODO: API 키 삭제"""
    pass
```

**평가 기준**:
- [ ] API 키 생성/조회/삭제 (30점)
- [ ] API 키 인증 동작 (30점)
- [ ] JWT와 API Key 동시 지원 (20점)
- [ ] 보안 (키 노출 방지) (10점)
- [ ] 테스트 작성 (10점)

---

### Day 3: 미들웨어 & 에러 처리 (6시간)

#### 🎯 학습 목표
- 로깅 미들웨어로 모든 요청 추적
- 전역 에러 핸들러
- Request ID로 분산 추적

#### 💻 실습 5: 로깅 미들웨어 (3시간)

**Request ID 미들웨어** (`middleware/request_id.py`):

```python
"""
Request ID middleware for distributed tracing.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request.

    - Generates UUID for each request
    - Adds to request.state for access in routes
    - Adds to response headers
    - Adds to all log messages
    """

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Add to request state
        request.state.request_id = request_id

        # Add to logging context
        with logger.contextualize(request_id=request_id):
            # Process request
            response = await call_next(request)

            # Add to response headers
            response.headers["X-Request-ID"] = request_id

            return response
```

**로깅 미들웨어** (`middleware/logging.py`):

```python
"""
Logging middleware for request/response logging.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

            # Add duration header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e)
                },
                exc_info=True
            )

            raise
```

**미들웨어 등록 순서** (`main.py`):

```python
# Middleware order matters! (LIFO order)
# Last added = first executed

# 1. Security headers (first)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request ID (before logging)
app.add_middleware(RequestIDMiddleware)

# 3. Logging (after request ID)
app.add_middleware(LoggingMiddleware)

# 4. CORS (before rate limiting)
app.add_middleware(CORSMiddleware, ...)

# 5. Rate limiting (last)
app.add_middleware(SlowAPIMiddleware)
```

#### 💻 실습 6: 전역 에러 핸들러 (2시간)

```python
"""
Custom exception handlers.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
import logging

logger = logging.getLogger(__name__)


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.

    Returns 422 with detailed validation errors.
    """
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors()
        }
    )


# Database error handler
@app.exception_handler(IntegrityError)
async def database_integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handle database integrity errors (unique constraints, foreign keys, etc).
    """
    logger.error(
        "Database integrity error",
        extra={"path": request.url.path},
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Database constraint violation",
            "detail": "The operation conflicts with existing data"
        }
    )


@app.exception_handler(OperationalError)
async def database_operational_error_handler(request: Request, exc: OperationalError):
    """
    Handle database operational errors (connection, etc).
    """
    logger.critical(
        "Database operational error",
        extra={"path": request.url.path},
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Database unavailable",
            "detail": "Please try again later"
        }
    )


# Custom exceptions
class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits."""
    pass


class OptimizationFailedError(Exception):
    """Raised when optimization fails."""
    pass


@app.exception_handler(InsufficientCreditsError)
async def insufficient_credits_handler(request: Request, exc: InsufficientCreditsError):
    """Handle insufficient credits error."""
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={
            "error": "Insufficient credits",
            "detail": str(exc)
        }
    )


@app.exception_handler(OptimizationFailedError)
async def optimization_failed_handler(request: Request, exc: OptimizationFailedError):
    """Handle optimization failure."""
    logger.error("Optimization failed", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Optimization failed",
            "detail": "Unable to optimize context. Please try again."
        }
    )
```

---

### Day 4: 통합 테스트 & 배포 준비 (6시간)

#### 💻 실습 7: 통합 테스트 (3시간)

```python
"""
tests/test_integration.py

End-to-end integration tests.
"""
import pytest
from fastapi.testclient import TestClient


class TestOptimizationFlow:
    """Test complete optimization flow."""

    def test_full_optimization_flow(self, client: TestClient):
        """
        TODO: 전체 플로우 테스트

        1. 회원가입
        2. 로그인 (토큰 받기)
        3. 최적화 요청
        4. 최적화 이력 조회
        5. 프로필 생성
        """
        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123"
            }
        )
        assert register_response.status_code == 201

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "TestPass123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Optimize
        optimize_response = client.post(
            "/api/v1/optimize",
            json={
                "query": "What is context engineering?",
                "context": "Context engineering is..." * 100,
                "model": "gpt-4-turbo",
                "max_tokens": 4000,
                "strategy": "hybrid"
            },
            headers=headers
        )
        assert optimize_response.status_code == 200
        data = optimize_response.json()
        assert "optimized_context" in data
        assert data["metrics"]["reduction_ratio"] > 0

        # 4. Get history
        history_response = client.get("/api/v1/optimize/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) == 1
        assert history[0]["request_id"] == data["request_id"]

        # 5. Create profile
        profile_response = client.post(
            "/api/v1/profiles",
            json={"name": "My Profile", "default_model": "gpt-4"},
            headers=headers
        )
        assert profile_response.status_code == 200


    def test_rate_limiting(self, client: TestClient):
        """
        TODO: Rate limiting 테스트

        1. 로그인
        2. 11번 연속 요청 (limit: 10/minute)
        3. 11번째 요청은 429 에러
        """
        # TODO: 구현


    def test_api_key_authentication(self, client: TestClient):
        """
        TODO: API Key 인증 테스트

        1. 로그인
        2. API 키 생성
        3. API 키로 요청 (JWT 없이)
        4. 성공 확인
        """
        # TODO: 구현
```

#### 💻 실습 8: Docker 이미지 빌드 (3시간)

**Dockerfile**:

```dockerfile
# Multi-stage build for smaller image size

# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/contextdb
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=contextdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

**빌드 및 실행**:

```bash
# Build image
docker build -t context-api:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f api

# Health check
curl http://localhost:8000/health

# Stop
docker-compose down
```

---

## ✅ Week 5-6 체크리스트

### 기술 역량
- [ ] FastAPI로 RESTful API 구축
- [ ] Pydantic으로 입력/출력 검증
- [ ] JWT 인증 시스템 구현
- [ ] Rate limiting 구현
- [ ] CORS 설정
- [ ] 미들웨어 작성
- [ ] 전역 에러 핸들링
- [ ] 통합 테스트 작성
- [ ] Docker 이미지 빌드

### 완료한 실습
- [ ] Exercise 1: CRUD API 구현
- [ ] Exercise 2: 인증 테스트 작성
- [ ] Exercise 3: API 키 인증 구현
- [ ] Exercise 4: Rate limiting 테스트
- [ ] Exercise 5: 통합 테스트

### 프로덕션 준비도
- [ ] 모든 엔드포인트에 인증 적용
- [ ] 적절한 Rate limit 설정
- [ ] HTTPS 준비 (프로덕션)
- [ ] 보안 헤더 적용
- [ ] 에러 응답이 일관적
- [ ] API 문서 (Swagger) 완성
- [ ] Docker로 로컬 실행 성공

---

## 📚 추가 학습 자료

### FastAPI 심화
- [FastAPI Advanced User Guide](https://fastapi.tiangolo.com/advanced/)
- [Dependency Injection Deep Dive](https://fastapi.tiangolo.com/advanced/advanced-dependencies/)
- [Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### 보안
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://curity.io/resources/learn/jwt-best-practices/)
- [Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

### 테스팅
- [pytest Advanced Features](https://docs.pytest.org/en/stable/how-to/index.html)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

## 🎓 평가 기준

| 항목 | 배점 | 평가 기준 |
|------|------|-----------|
| **기능 구현** | 40점 | 모든 실습 완료 |
| **코드 품질** | 20점 | 구조, 네이밍, 문서화 |
| **테스트** | 20점 | 커버리지, Edge cases |
| **보안** | 10점 | 인증, Rate limiting, 보안 헤더 |
| **배포** | 10점 | Docker 빌드 성공 |

**합격 기준**: 70점 이상

---

## 다음 단계

Week 5-6을 완료했다면:

✅ **Week 7-8로 이동**: Kubernetes 배포, Prometheus 모니터링, Grafana 대시보드

💡 **복습 권장**: 특히 JWT 인증과 Rate limiting은 매우 중요!

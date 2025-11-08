# Final Project: Smart Context Optimizer API

## 개요

**10주 학습의 집대성**: 실제 회사에서 사용 가능한 완전한 프로덕션 시스템 구축

**프로젝트 목표**:
완전한 Context Engineering SaaS API를 처음부터 끝까지 구축하고 프로덕션에 배포합니다.

**예상 시간**: 40-60시간 (2주)

## 프로젝트 요구사항

### 기능 요구사항

#### 1. 사용자 관리
- [ ] 사용자 가입/로그인 (JWT)
- [ ] API 키 발급 및 관리
- [ ] 사용량 쿼터 관리 (월별)
- [ ] 사용량 알람

#### 2. Context Optimization API
- [ ] POST /api/v1/optimize - 단일 최적화
- [ ] POST /api/v1/batch - 배치 최적화
- [ ] GET /api/v1/strategies - 사용 가능한 전략 목록
- [ ] GET /api/v1/usage - 사용량 조회
- [ ] GET /api/v1/analytics - 비용 분석

#### 3. 최적화 전략
- [ ] 컨텍스트 압축 (3가지 이상)
- [ ] 우선순위화 (관련성, 최신성, 중요도)
- [ ] 동적 조립
- [ ] A/B 테스팅

#### 4. 모니터링 & 운영
- [ ] Prometheus 메트릭
- [ ] Grafana 대시보드
- [ ] 에러 추적 (Sentry)
- [ ] 로그 집계

### 비기능 요구사항

#### 성능
- [ ] p95 latency < 500ms
- [ ] 처리량 > 100 req/s
- [ ] 캐시 히트율 > 60%

#### 안정성
- [ ] 99.9% uptime
- [ ] 자동 재시도
- [ ] Circuit breaker
- [ ] Graceful degradation

#### 보안
- [ ] JWT 인증
- [ ] Rate limiting (per user)
- [ ] Input validation
- [ ] SQL injection 방지
- [ ] HTTPS 강제

#### 품질
- [ ] 80%+ 테스트 커버리지
- [ ] CI/CD 파이프라인
- [ ] 코드 리뷰
- [ ] 문서화

## 아키텍처

### 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
│                      (NGINX / Ingress)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼─────┐  ┌────────▼─────┐
│   API Pod 1  │  │  API Pod 2   │  │  API Pod 3   │
│              │  │              │  │              │
│  FastAPI     │  │  FastAPI     │  │  FastAPI     │
│  + Workers   │  │  + Workers   │  │  + Workers   │
└───────┬──────┘  └────────┬─────┘  └────────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────┐                  ┌───────────▼──────┐
│  PostgreSQL  │                  │     Redis        │
│              │                  │                  │
│  • Users     │                  │  • Cache         │
│  • QueryLogs │                  │  • Sessions      │
│  • Metrics   │                  │  • Rate Limits   │
└──────────────┘                  └──────────────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
┌──────────────────────────▼───────────────────────────┐
│                  Monitoring Stack                    │
│                                                       │
│  Prometheus  →  Grafana  →  AlertManager             │
│  Loki        →  Grafana                              │
│  Sentry      (Error Tracking)                        │
└───────────────────────────────────────────────────────┘
```

### 데이터 모델

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    quota_limit DECIMAL(10,2) DEFAULT 100.00,
    quota_used DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query Logs
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    request_id VARCHAR(64) UNIQUE NOT NULL,
    query TEXT,
    context_tokens INTEGER,
    response_tokens INTEGER,
    model VARCHAR(50),
    strategy VARCHAR(50),
    cost DECIMAL(10,4),
    latency_ms DECIMAL(10,2),
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_logs_user_created ON query_logs(user_id, created_at);
CREATE INDEX idx_query_logs_request ON query_logs(request_id);

-- API Keys
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(100),
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE
);

-- Cost Metrics (시간별 집계)
CREATE TABLE cost_metrics (
    id SERIAL PRIMARY KEY,
    hour_timestamp TIMESTAMP NOT NULL,
    total_queries INTEGER,
    total_cost DECIMAL(10,2),
    cache_hit_rate DECIMAL(5,2),
    avg_latency_ms DECIMAL(10,2)
);

CREATE UNIQUE INDEX idx_cost_metrics_hour ON cost_metrics(hour_timestamp);
```

## 구현 단계

### Week 1: Core API (주당 30시간)

#### Day 1-2: 프로젝트 구조 설정 (12시간)

```bash
smart-context-optimizer/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── dependencies.py         # DI
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 인증 endpoints
│   │   │   ├── optimize.py     # 최적화 endpoints
│   │   │   ├── analytics.py    # 분석 endpoints
│   │   │   └── users.py        # 사용자 endpoints
│   │   └── middleware/
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       └── logging.py
│   │
│   ├── core/
│   │   ├── security.py         # JWT, hashing
│   │   ├── optimizer.py        # Core logic
│   │   └── strategies/
│   │       ├── compression.py
│   │       ├── prioritization.py
│   │       └── assembly.py
│   │
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   │
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── cache_client.py
│   │   └── analytics.py
│   │
│   └── utils/
│       ├── logging.py
│       ├── monitoring.py
│       └── errors.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── alembic/                    # DB migrations
├── k8s/                        # Kubernetes manifests
├── monitoring/                 # Prometheus, Grafana configs
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

**체크리스트**:
- [ ] 프로젝트 구조 생성
- [ ] FastAPI 앱 초기화
- [ ] Settings 설정 (Pydantic)
- [ ] Docker compose 설정
- [ ] PostgreSQL, Redis 연결

#### Day 3-4: 인증 시스템 (12시간)

```python
# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.schemas import UserCreate, Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    TODO: 회원가입

    1. 이메일 중복 확인
    2. 비밀번호 해싱
    3. API 키 생성
    4. User 생성
    5. JWT 토큰 반환
    """
    pass


@router.post("/login", response_model=Token)
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """
    TODO: 로그인

    1. User 조회
    2. 비밀번호 검증
    3. JWT 토큰 생성 및 반환
    """
    pass


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user = Depends(get_current_user)):
    """TODO: 토큰 갱신"""
    pass
```

**체크리스트**:
- [ ] JWT 토큰 생성/검증
- [ ] 비밀번호 해싱 (bcrypt)
- [ ] 회원가입 endpoint
- [ ] 로그인 endpoint
- [ ] 토큰 갱신 endpoint
- [ ] 테스트 작성

#### Day 5-7: 최적화 API (18시간)

```python
# app/api/v1/optimize.py

from fastapi import APIRouter, Depends
from app.models.schemas import OptimizeRequest, OptimizeResponse
from app.core.optimizer import ContextOptimizer

router = APIRouter(prefix="/optimize", tags=["optimization"])

@router.post("/", response_model=OptimizeResponse)
async def optimize(
    request: OptimizeRequest,
    current_user = Depends(get_current_user),
    optimizer: ContextOptimizer = Depends(get_optimizer)
):
    """
    TODO: 단일 최적화

    1. Quota 확인
    2. 최적화 수행
    3. 로그 저장
    4. Quota 업데이트
    5. 결과 반환
    """
    pass


@router.post("/batch", response_model=list[OptimizeResponse])
async def batch_optimize(
    requests: list[OptimizeRequest],
    current_user = Depends(get_current_user),
    optimizer: ContextOptimizer = Depends(get_optimizer)
):
    """
    TODO: 배치 최적화

    1. 모든 요청 병렬 처리
    2. 결과 집계
    """
    import asyncio
    tasks = [optimizer.optimize_async(req) for req in requests]
    results = await asyncio.gather(*tasks)
    return results


@router.get("/strategies")
async def list_strategies():
    """사용 가능한 전략 목록"""
    return {
        "compression": ["extractive", "semantic", "hybrid"],
        "prioritization": ["relevance", "recency", "importance"],
        "assembly": ["query_aware", "adaptive"]
    }
```

**체크리스트**:
- [ ] 단일 최적화 endpoint
- [ ] 배치 최적화 endpoint
- [ ] 전략 선택 기능
- [ ] 에러 핸들링
- [ ] Rate limiting
- [ ] 테스트 작성 (unit + integration)

### Week 2: 배포 & 모니터링 (주당 30시간)

#### Day 1-2: Docker & Kubernetes (12시간)

```dockerfile
# Dockerfile (Multi-stage build)

FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: context-optimizer-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: context-optimizer
  template:
    metadata:
      labels:
        app: context-optimizer
    spec:
      containers:
      - name: api
        image: your-registry/context-optimizer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**체크리스트**:
- [ ] Multi-stage Dockerfile
- [ ] Docker compose (local dev)
- [ ] Kubernetes manifests
- [ ] Secrets management
- [ ] Health checks
- [ ] Resource limits

#### Day 3-5: 모니터링 (18시간)

```python
# app/utils/monitoring.py

from prometheus_client import Counter, Histogram, Gauge

# Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

optimization_latency_seconds = Histogram(
    'optimization_latency_seconds',
    'Optimization latency',
    ['strategy']
)

optimization_cost_dollars = Histogram(
    'optimization_cost_dollars',
    'Optimization cost',
    ['model']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate'
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)


# Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from time import time

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time()

        response = await call_next(request)

        latency = time() - start_time

        api_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        return response
```

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'context-optimizer'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: context-optimizer
        action: keep
```

```json
// monitoring/grafana-dashboard.json

{
  "dashboard": {
    "title": "Context Optimizer Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {"expr": "rate(api_requests_total[5m])"}
        ]
      },
      {
        "title": "Latency (p95)",
        "targets": [
          {"expr": "histogram_quantile(0.95, optimization_latency_seconds)"}
        ]
      },
      {
        "title": "Cost per Hour",
        "targets": [
          {"expr": "sum(rate(optimization_cost_dollars[1h]))"}
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {"expr": "cache_hit_rate"}
        ]
      }
    ]
  }
}
```

**체크리스트**:
- [ ] Prometheus 메트릭
- [ ] Grafana 대시보드
- [ ] Alert rules
- [ ] Log aggregation (Loki)
- [ ] Error tracking (Sentry)

#### Day 6-7: CI/CD (12시간)

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.REGISTRY }}/context-optimizer:${{ github.sha }} .

      - name: Push to registry
        run: |
          docker push ${{ secrets.REGISTRY }}/context-optimizer:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/context-optimizer-api \
            api=${{ secrets.REGISTRY }}/context-optimizer:${{ github.sha }}

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/context-optimizer-api
```

**체크리스트**:
- [ ] 자동 테스트
- [ ] Docker 이미지 빌드
- [ ] Registry push
- [ ] K8s 배포
- [ ] Rollback 전략

## 평가 기준

### 기능 완성도 (40점)
- [ ] 모든 API endpoint 구현 (10점)
- [ ] 3가지 이상 최적화 전략 (10점)
- [ ] 사용자 인증 및 권한 (10점)
- [ ] 분석 및 리포팅 (10점)

### 성능 (20점)
- [ ] p95 latency < 500ms (5점)
- [ ] 처리량 > 100 req/s (5점)
- [ ] 캐시 히트율 > 60% (5점)
- [ ] 99.9% uptime (5점)

### 코드 품질 (20점)
- [ ] 80%+ 테스트 커버리지 (10점)
- [ ] 코드 스타일 일관성 (5점)
- [ ] 문서화 완성도 (5점)

### 운영 준비도 (20점)
- [ ] K8s 배포 성공 (5점)
- [ ] 모니터링 대시보드 (5점)
- [ ] CI/CD 파이프라인 (5점)
- [ ] 에러 추적 (5점)

## 제출물

### 1. 코드 저장소
```
https://github.com/your-username/smart-context-optimizer
```

필수 파일:
- [ ] README.md (설치 및 실행 가이드)
- [ ] API 문서 (OpenAPI/Swagger)
- [ ] 아키텍처 다이어그램
- [ ] 배포 가이드

### 2. 라이브 데모
```
https://context-optimizer.your-domain.com

API Key: (제공)
```

### 3. 발표 자료 (10-15분)
1. 프로젝트 개요
2. 아키텍처 설명
3. 주요 기술 결정
4. 성능 메트릭
5. 배운 점 및 개선 사항
6. 라이브 데모

### 4. 기술 문서
- [ ] 시스템 아키텍처
- [ ] API 사용 가이드
- [ ] 배포 가이드
- [ ] 트러블슈팅 가이드

## 성공 사례

### 목표 달성
- ✅ 99.9% uptime (43분 다운타임/월)
- ✅ p95 latency 234ms
- ✅ 처리량 150 req/s
- ✅ 캐시 히트율 72%
- ✅ 테스트 커버리지 87%
- ✅ 비용 절감 65%

## 다음 단계

### 프로젝트 완료 후
1. **포트폴리오에 추가**
   - GitHub README 다듬기
   - 블로그 포스팅
   - LinkedIn 프로필 업데이트

2. **실제 배포**
   - 무료 티어로 시작 (AWS Free Tier, GCP)
   - 친구들에게 테스트 요청
   - 피드백 수집 및 개선

3. **오픈소스 기여**
   - 관련 프로젝트에 기여
   - 자신의 프로젝트 오픈소스화

4. **추가 학습**
   - Microservices 아키텍처
   - Event-driven architecture
   - Machine Learning Ops

## 리소스

### 참고 자료
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

### 커뮤니티
- GitHub Discussions
- Stack Overflow
- Discord 커뮤니티

---

**🎉 축하합니다!**

10주 학습을 완료하고 프로덕션 시스템을 구축했습니다.

이제 당신은:
- ✅ 프로덕션 수준의 시스템을 설계할 수 있습니다
- ✅ 안정적이고 확장 가능한 API를 만들 수 있습니다
- ✅ 모니터링과 운영을 할 수 있습니다
- ✅ 실제 회사에서 바로 사용 가능한 기술을 갖췄습니다

**다음 목표**: 실제 프로덕션 환경에서 운영 경험 쌓기! 🚀

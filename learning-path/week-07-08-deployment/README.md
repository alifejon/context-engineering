# Week 7-8: Deployment & Monitoring

**학습 기간**: 2주 (38시간)
**목표**: Kubernetes 배포 + Prometheus/Grafana 모니터링 + 로그 집계

## 📋 학습 목표

이 2주 과정을 마치면 다음을 할 수 있습니다:

- ✅ Docker 컨테이너화
- ✅ Kubernetes 클러스터에 배포
- ✅ Prometheus로 메트릭 수집
- ✅ Grafana 대시보드 구축
- ✅ 중앙집중식 로깅 (ELK/Loki)
- ✅ Health check & Readiness probe
- ✅ Horizontal Pod Autoscaling
- ✅ Blue-Green/Canary 배포

## 🎯 필수 선수 지식

- Week 1-6 완료
- Docker 기초 (컨테이너, 이미지, 레지스트리)
- Kubernetes 기본 개념 (Pod, Service, Deployment)
- YAML 문법
- Linux 기본 명령어

## 📚 학습 자료

### 공식 문서
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Helm Charts](https://helm.sh/docs/)

### 추천 튜토리얼
- [Kubernetes By Example](https://kubernetesbyexample.com/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [FastAPI + Kubernetes Guide](https://testdriven.io/blog/fastapi-kubernetes/)

## 📅 2주 학습 계획

```
Week 7 (18시간)
├── Day 1-2: Docker & Kubernetes 기초 (10시간)
│   ├── Multi-stage Dockerfile 최적화
│   ├── Kubernetes 리소스 정의 (Deployment, Service, ConfigMap)
│   ├── Ingress 설정
│   └── Secret 관리
│
└── Day 3-4: 배포 전략 & Health Checks (8시간)
    ├── Liveness/Readiness probes
    ├── Rolling update
    ├── Blue-Green 배포
    └── Horizontal Pod Autoscaler

Week 8 (20시간)
├── Day 1-2: Prometheus 메트릭 (10시간)
│   ├── prometheus-client 통합
│   ├── Custom metrics 정의
│   ├── ServiceMonitor 설정
│   └── Alert rules
│
├── Day 3: Grafana 대시보드 (5시간)
│   ├── 데이터 소스 연결
│   ├── 대시보드 구축
│   └── Alert 통합
│
└── Day 4: 로깅 & 트러블슈팅 (5시간)
    ├── Structured logging
    ├── Loki 또는 ELK
    └── 분산 추적 (Jaeger)
```

---

## Week 7: Kubernetes 배포

### Day 1-2: Docker & Kubernetes 기초 (10시간)

#### 🎯 학습 목표
- 프로덕션급 Dockerfile 작성
- Kubernetes 리소스 정의
- ConfigMap/Secret 관리
- Ingress 설정

#### 📖 이론: Kubernetes 아키텍처

**핵심 구성 요소**:

```
Kubernetes Cluster
├── Control Plane
│   ├── API Server: 모든 요청의 진입점
│   ├── Scheduler: Pod를 노드에 할당
│   ├── Controller Manager: 리소스 상태 관리
│   └── etcd: 클러스터 상태 저장
│
└── Worker Nodes
    ├── kubelet: Pod 생성/관리
    ├── kube-proxy: 네트워크 라우팅
    └── Container Runtime: Docker/containerd
```

**주요 리소스**:

| 리소스 | 용도 | 예시 |
|--------|------|------|
| **Pod** | 최소 배포 단위 (컨테이너 그룹) | 1개의 API 컨테이너 |
| **Deployment** | Pod 복제 및 롤링 업데이트 | API 서버 3개 replica |
| **Service** | Pod 접근을 위한 네트워크 엔드포인트 | api-service:8000 |
| **ConfigMap** | 설정 파일 저장 | 환경변수, 설정 파일 |
| **Secret** | 민감 정보 저장 (암호화) | API 키, DB 비밀번호 |
| **Ingress** | 외부 → 서비스 라우팅 (L7) | app.example.com → api-service |
| **PersistentVolume** | 영구 스토리지 | PostgreSQL 데이터 |

#### 💻 실습 1: 프로덕션 Dockerfile (2시간)

**최적화된 Multi-stage Dockerfile**:

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: Base image with dependencies
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user (don't run as root!)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# Stage 3: Development
FROM base as development

# Copy dependencies from previous stage
COPY --from=dependencies /root/.local /root/.local

# Copy application code
COPY . .

# Set environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development

# Expose port
EXPOSE 8000

# Run with reload
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Production
FROM base as production

# Copy dependencies
COPY --from=dependencies /root/.local /root/.local

# Copy application code
COPY . .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**주요 최적화**:

1. **Multi-stage build**:
   - 최종 이미지 크기 감소 (build dependencies 제외)
   - 개발/프로덕션 분리

2. **Non-root user**:
   - 보안: 컨테이너가 root로 실행되지 않음

3. **Layer caching**:
   - requirements.txt를 먼저 COPY → 코드 변경 시 의존성 재설치 안 함

4. **Health check**:
   - 컨테이너 상태 자동 확인

**빌드 및 실행**:

```bash
# Development build
docker build --target development -t context-api:dev .
docker run -p 8000:8000 context-api:dev

# Production build
docker build --target production -t context-api:prod .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... context-api:prod

# Multi-platform build (Apple Silicon → x86_64)
docker buildx build --platform linux/amd64 -t context-api:prod .
```

#### 💻 실습 2: Kubernetes 리소스 정의 (4시간)

**디렉토리 구조**:

```
k8s/
├── namespace.yaml
├── configmap.yaml
├── secret.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
├── hpa.yaml                 # Horizontal Pod Autoscaler
└── postgres/
    ├── statefulset.yaml
    ├── service.yaml
    └── pvc.yaml            # PersistentVolumeClaim
```

**1. Namespace** (`k8s/namespace.yaml`):

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: context-engineering
  labels:
    name: context-engineering
    environment: production
```

**2. ConfigMap** (`k8s/configmap.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: context-engineering
data:
  # Application settings
  APP_NAME: "Context Optimization API"
  APP_VERSION: "1.0.0"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"

  # API settings
  API_V1_PREFIX: "/api/v1"
  RATE_LIMIT_PER_MINUTE: "60"

  # JWT settings
  ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"

  # CORS
  CORS_ORIGINS: '["https://app.example.com"]'

  # Database (non-sensitive parts)
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "contextdb"

  # Redis
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
```

**3. Secret** (`k8s/secret.yaml`):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: context-engineering
type: Opaque
stringData:
  # OpenAI API key
  OPENAI_API_KEY: "sk-..."

  # JWT secret (generate with: openssl rand -hex 32)
  SECRET_KEY: "your-secret-key-here"

  # Database credentials
  DATABASE_USER: "contextuser"
  DATABASE_PASSWORD: "strong-password-here"

  # Connection strings (built from above)
  DATABASE_URL: "postgresql://contextuser:strong-password-here@postgres-service:5432/contextdb"
  REDIS_URL: "redis://redis-service:6379/0"
```

**생성 방법**:

```bash
# From literal values
kubectl create secret generic api-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  -n context-engineering

# From .env file
kubectl create secret generic api-secrets \
  --from-env-file=.env.production \
  -n context-engineering
```

**4. Deployment** (`k8s/deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
  namespace: context-engineering
  labels:
    app: context-api
    version: v1
spec:
  replicas: 3  # 3 pods for high availability
  selector:
    matchLabels:
      app: context-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 최대 1개 pod 추가 생성
      maxUnavailable: 0    # 항상 최소 3개 실행 유지
  template:
    metadata:
      labels:
        app: context-api
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      # Init container (wait for database)
      initContainers:
        - name: wait-for-db
          image: postgres:15-alpine
          command:
            - sh
            - -c
            - |
              until pg_isready -h postgres-service -p 5432; do
                echo "Waiting for database..."
                sleep 2
              done
          env:
            - name: PGHOST
              value: postgres-service

      # Main container
      containers:
        - name: api
          image: your-registry/context-api:v1.0.0
          imagePullPolicy: IfNotPresent

          ports:
            - name: http
              containerPort: 8000
              protocol: TCP

          # Environment variables from ConfigMap
          envFrom:
            - configMapRef:
                name: api-config
            - secretRef:
                name: api-secrets

          # Resource limits
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"      # 0.25 CPU
            limits:
              memory: "512Mi"
              cpu: "500m"      # 0.5 CPU

          # Liveness probe (restart if unhealthy)
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3

          # Readiness probe (don't route traffic if not ready)
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3

          # Startup probe (for slow-starting apps)
          startupProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 0
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 30  # 150초 (30 * 5) 내에 시작

      # Restart policy
      restartPolicy: Always
```

**Probe 종류**:

| Probe | 용도 | 실패 시 동작 |
|-------|------|-------------|
| **Liveness** | 컨테이너가 살아있는지 | Pod 재시작 |
| **Readiness** | 트래픽 받을 준비가 되었는지 | 트래픽 차단 |
| **Startup** | 앱이 시작되었는지 | Pod 재시작 |

**5. Service** (`k8s/service.yaml`):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: context-engineering
  labels:
    app: context-api
spec:
  type: ClusterIP  # Internal only (use Ingress for external)
  selector:
    app: context-api
  ports:
    - name: http
      protocol: TCP
      port: 80       # Service port
      targetPort: 8000  # Container port
  sessionAffinity: None
```

**Service types**:

| Type | 용도 | 접근 방법 |
|------|------|-----------|
| **ClusterIP** | 클러스터 내부만 | 다른 Pod에서 접근 |
| **NodePort** | 외부 접근 (각 노드의 포트) | node-ip:30000 |
| **LoadBalancer** | 클라우드 로드밸런서 | 외부 IP |
| **ExternalName** | 외부 서비스에 DNS alias | CNAME |

**6. Ingress** (`k8s/ingress.yaml`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: context-engineering
  annotations:
    # nginx ingress controller settings
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"  # requests per second
    nginx.ingress.kubernetes.io/limit-rps: "100"

    # cert-manager (Let's Encrypt)
    cert-manager.io/cluster-issuer: "letsencrypt-prod"

spec:
  ingressClassName: nginx

  # TLS settings
  tls:
    - hosts:
        - api.example.com
      secretName: api-tls-cert

  # Routing rules
  rules:
    - host: api.example.com
      http:
        paths:
          # API endpoints
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80

          # Health check
          - path: /health
            pathType: Exact
            backend:
              service:
                name: api-service
                port:
                  number: 80

          # Docs
          - path: /docs
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80
```

**배포 명령어**:

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create ConfigMap and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get all -n context-engineering

# View logs
kubectl logs -f deployment/api-deployment -n context-engineering

# Describe pod
kubectl describe pod <pod-name> -n context-engineering
```

#### ✍️ Exercise 1: PostgreSQL StatefulSet 구현 (3시간)

**목표**: Kubernetes에서 상태를 가진 애플리케이션(PostgreSQL) 배포

**요구사항**:

```yaml
# k8s/postgres/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: context-engineering
spec:
  serviceName: "postgres-headless"
  replicas: 1  # TODO: 프로덕션에서는 3 (replication)
  selector:
    matchLabels:
      app: postgres

  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
              name: postgres

          env:
            # TODO: Secret에서 가져오기
            - name: POSTGRES_DB
              value: contextdb
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: DATABASE_USER
            # ... more env vars

          # TODO: Volume mount
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data

          # TODO: Liveness/Readiness probes
          # Hint: exec: ["pg_isready", "-U", "postgres"]

          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"

  # TODO: VolumeClaimTemplates
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
        # storageClassName: fast-ssd  # 클라우드 제공자에 따라
```

```yaml
# k8s/postgres/service.yaml
# TODO: Headless Service 정의
# Hint: clusterIP: None
```

**테스트**:

```bash
# Deploy
kubectl apply -f k8s/postgres/

# Check PVC (PersistentVolumeClaim)
kubectl get pvc -n context-engineering

# Connect to PostgreSQL
kubectl exec -it postgres-0 -n context-engineering -- psql -U contextuser -d contextdb

# Test data persistence
# 1. Insert data
# 2. Delete pod
# 3. Check data still exists
```

---

### Day 3-4: 배포 전략 & Autoscaling (8시간)

#### 📖 이론: 배포 전략

**1. Rolling Update (기본값)**:

```
v1: ███████████░░░  (3 pods → 2 pods)
v2: ░░░░░░░░███████  (0 → 3 pods)

Process:
1. v2 pod 1개 생성
2. 정상 확인 (readiness probe)
3. v1 pod 1개 삭제
4. 반복
```

**장점**: 다운타임 없음
**단점**: 일시적으로 v1/v2 혼재

**2. Blue-Green 배포**:

```
Blue (v1):  ███████████  (100% traffic)
Green (v2): ███████████  (0% traffic)

→ Switch →

Blue (v1):  ███████████  (0% traffic)
Green (v2): ███████████  (100% traffic)
```

**장점**: 즉시 롤백 가능
**단점**: 2배 리소스 필요

**3. Canary 배포**:

```
v1: ███████████  (90% traffic)
v2: █            (10% traffic)

→ Monitor →

v1: ░░░░░░░░░░░  (0% traffic)
v2: ███████████  (100% traffic)
```

**장점**: 점진적 롤아웃, 리스크 감소
**단점**: 트래픽 분할 복잡

#### 💻 실습 3: Horizontal Pod Autoscaler (2시간)

**HPA 정의** (`k8s/hpa.yaml`):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: context-engineering
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment

  minReplicas: 3
  maxReplicas: 10

  metrics:
    # CPU 기반
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # CPU 70% 넘으면 스케일 아웃

    # Memory 기반
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metric (예: 요청 수)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"  # Pod당 1000 req/s 넘으면 스케일 아웃

  # 스케일 동작 설정
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5분간 메트릭 안정화 후 스케일 다운
      policies:
        - type: Percent
          value: 50  # 한 번에 최대 50% 감소
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0  # 즉시 스케일 업
      policies:
        - type: Percent
          value: 100  # 한 번에 최대 100% 증가 (2배)
          periodSeconds: 15
```

**Metrics Server 설치**:

```bash
# Metrics Server (CPU/Memory metrics 수집)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# HPA 적용
kubectl apply -f k8s/hpa.yaml

# HPA 상태 확인
kubectl get hpa -n context-engineering
kubectl describe hpa api-hpa -n context-engineering
```

**부하 테스트**:

```bash
# Apache Bench
ab -n 10000 -c 100 https://api.example.com/api/v1/optimize

# 또는 k6
k6 run load-test.js

# HPA 동작 확인
watch kubectl get hpa,pods -n context-engineering
```

#### 💻 실습 4: Blue-Green 배포 (3시간)

**Blue Deployment** (현재 버전):

```yaml
# k8s/deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment-blue
  namespace: context-engineering
spec:
  replicas: 3
  selector:
    matchLabels:
      app: context-api
      version: blue
  template:
    metadata:
      labels:
        app: context-api
        version: blue
    spec:
      containers:
        - name: api
          image: your-registry/context-api:v1.0.0
          # ... rest of spec
```

**Green Deployment** (새 버전):

```yaml
# k8s/deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment-green
  namespace: context-engineering
spec:
  replicas: 3
  selector:
    matchLabels:
      app: context-api
      version: green
  template:
    metadata:
      labels:
        app: context-api
        version: green
    spec:
      containers:
        - name: api
          image: your-registry/context-api:v1.1.0  # New version!
          # ... rest of spec
```

**Service (트래픽 라우팅)**:

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: context-engineering
spec:
  selector:
    app: context-api
    version: blue  # Switch to "green" for deployment
  ports:
    - port: 80
      targetPort: 8000
```

**배포 프로세스**:

```bash
# 1. Blue 배포 (현재)
kubectl apply -f k8s/deployment-blue.yaml

# 2. Green 배포 (새 버전, 트래픽 없음)
kubectl apply -f k8s/deployment-green.yaml

# 3. Green 상태 확인
kubectl rollout status deployment/api-deployment-green -n context-engineering
kubectl get pods -l version=green -n context-engineering

# 4. Smoke test (내부에서만 테스트)
kubectl run -it --rm test-pod --image=curlimages/curl --restart=Never -- \
  curl http://api-deployment-green:8000/health

# 5. 트래픽 스위치 (Blue → Green)
kubectl patch service api-service -n context-engineering \
  -p '{"spec":{"selector":{"version":"green"}}}'

# 6. 모니터링 (5-10분)
# - 에러율 확인
# - Latency 확인
# - 로그 확인

# 7a. 성공 → Blue 삭제
kubectl delete deployment api-deployment-blue -n context-engineering

# 7b. 실패 → Rollback (Green → Blue)
kubectl patch service api-service -n context-engineering \
  -p '{"spec":{"selector":{"version":"blue"}}}'
kubectl delete deployment api-deployment-green -n context-engineering
```

---

## Week 8: Monitoring & Logging

### Day 1-2: Prometheus 메트릭 (10시간)

#### 📖 이론: Prometheus

**Prometheus 아키텍처**:

```
Application
    ↓ (exposes /metrics)
Prometheus Server
    ↓ (scrapes metrics every 15s)
Time-Series Database
    ↓ (queries)
Grafana Dashboard
```

**메트릭 타입**:

| Type | 설명 | 예시 | PromQL |
|------|------|------|--------|
| **Counter** | 증가만 하는 값 | 요청 수, 에러 수 | `rate(requests_total[5m])` |
| **Gauge** | 증가/감소하는 값 | CPU%, 메모리 사용량 | `memory_usage_bytes` |
| **Histogram** | 값의 분포 | 응답 시간, 요청 크기 | `histogram_quantile(0.95, latency_seconds)` |
| **Summary** | Histogram과 유사 | P95, P99 계산 | `latency_seconds{quantile="0.95"}` |

#### 💻 실습 5: Prometheus 통합 (4시간)

**1단계: prometheus-client 설치**

```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

**2단계: 메트릭 정의** (`api/metrics.py`):

```python
"""
Prometheus metrics for the API.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator

# Application info
app_info = Info('context_api', 'Context Optimization API')
app_info.info({'version': '1.0.0', 'environment': 'production'})

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]  # 10ms ~ 5s
)

# Business metrics
optimization_requests_total = Counter(
    'optimization_requests_total',
    'Total optimization requests',
    ['strategy', 'model']
)

optimization_duration_seconds = Histogram(
    'optimization_duration_seconds',
    'Optimization processing time',
    ['strategy'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

optimization_cost_dollars = Histogram(
    'optimization_cost_dollars',
    'Cost per optimization',
    ['model'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
)

token_reduction_ratio = Histogram(
    'token_reduction_ratio',
    'Token reduction ratio',
    ['strategy'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
)

# Cache metrics
cache_hits_total = Counter('cache_hits_total', 'Total cache hits')
cache_misses_total = Counter('cache_misses_total', 'Total cache misses')

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Current state (Gauges)
active_requests = Gauge('active_requests', 'Number of active requests')
database_connections = Gauge('database_connections', 'Number of database connections')
redis_connections = Gauge('redis_connections', 'Number of Redis connections')


def get_instrumentator():
    """Get FastAPI instrumentator with custom settings."""
    return Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True
    )
```

**3단계: FastAPI 통합** (`api/main.py`):

```python
from prometheus_client import make_asgi_app
from .metrics import get_instrumentator, optimization_requests_total, optimization_duration_seconds

# Create instrumentator
instrumentator = get_instrumentator()

# Instrument app (adds /metrics endpoint)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Alternative: Manual /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**4단계: 비즈니스 메트릭 추가** (`routers/optimize.py`):

```python
from ..metrics import (
    optimization_requests_total,
    optimization_duration_seconds,
    optimization_cost_dollars,
    token_reduction_ratio,
    active_requests
)
import time

@router.post("/optimize")
async def optimize_context(...):
    # Track active requests
    active_requests.inc()

    try:
        start_time = time.time()

        # ... optimization logic ...

        # Record metrics
        optimization_requests_total.labels(
            strategy=request.strategy,
            model=request.model
        ).inc()

        optimization_duration_seconds.labels(
            strategy=request.strategy
        ).observe(time.time() - start_time)

        optimization_cost_dollars.labels(
            model=result['model']
        ).observe(result['cost'])

        token_reduction_ratio.labels(
            strategy=request.strategy
        ).observe(result['reduction_ratio'])

        return response

    finally:
        active_requests.dec()
```

**5단계: Prometheus Operator 설치**:

```bash
# Add Prometheus Operator Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus Operator
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Check installation
kubectl get pods -n monitoring
```

**6단계: ServiceMonitor 정의** (`k8s/servicemonitor.yaml`):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-metrics
  namespace: context-engineering
  labels:
    app: context-api
spec:
  selector:
    matchLabels:
      app: context-api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s  # Scrape every 15 seconds
```

**PromQL 쿼리 예시**:

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(errors_total[5m]) / rate(http_requests_total[5m])

# Average cost per request
rate(optimization_cost_dollars_sum[1h]) / rate(optimization_cost_dollars_count[1h])

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Requests by strategy
sum by (strategy) (rate(optimization_requests_total[5m]))
```

#### ✍️ Exercise 2: Alert Rules 정의 (2시간)

**목표**: 이상 상황 자동 감지 및 알림

```yaml
# k8s/prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: context-engineering
spec:
  groups:
    - name: api_performance
      interval: 30s
      rules:
        # High error rate
        - alert: HighErrorRate
          expr: |
            (rate(errors_total[5m]) / rate(http_requests_total[5m])) > 0.05
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

        # TODO: High latency alert
        - alert: HighLatency
          expr: |
            # Hint: histogram_quantile(0.95, ...) > 2.0
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "High latency detected"

        # TODO: High cost rate
        - alert: HighCostRate
          expr: |
            # Hint: rate(optimization_cost_dollars_sum[1h]) > 100
          for: 1h
          labels:
            severity: critical
          annotations:
            summary: "Hourly cost exceeds $100"

        # TODO: Low cache hit rate
        - alert: LowCacheHitRate
          # Hint: cache_hits / (cache_hits + cache_misses) < 0.5

        # TODO: Pod down
        - alert: PodDown
          expr: kube_pod_status_phase{namespace="context-engineering",phase="Running"} == 0
```

---

### Day 3: Grafana 대시보드 (5시간)

#### 💻 실습 6: Grafana 대시보드 구축 (5시간)

**Grafana 접속**:

```bash
# Port forward
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Default credentials
# Username: admin
# Password: prom-operator
```

**대시보드 JSON** (`grafana-dashboard.json`):

```json
{
  "dashboard": {
    "title": "Context Optimization API",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{namespace=\"context-engineering\"}[5m]))",
            "legendFormat": "Requests/sec"
          }
        ],
        "type": "graph"
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(errors_total[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error %"
          }
        ],
        "thresholds": [
          {"value": 0.01, "color": "green"},
          {"value": 0.05, "color": "yellow"},
          {"value": 0.10, "color": "red"}
        ]
      }
    ]
  }
}
```

---

## ✅ Week 7-8 체크리스트

- [ ] 프로덕션 Dockerfile 작성
- [ ] Kubernetes 리소스 정의 (Deployment, Service, Ingress, ConfigMap, Secret)
- [ ] StatefulSet으로 PostgreSQL 배포
- [ ] HPA 설정
- [ ] Blue-Green 배포 실습
- [ ] Prometheus 메트릭 통합
- [ ] 비즈니스 메트릭 정의
- [ ] Alert rules 작성
- [ ] Grafana 대시보드 구축

---

## 다음 단계

✅ **Week 9-10로 이동**: 비동기 처리, 성능 최적화, 보안 강화

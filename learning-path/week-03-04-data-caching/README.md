# Week 3-4: Data & Caching

## 개요

프로덕션 시스템의 두 번째 기둥: **데이터 영속성과 성능 최적화**

**학습 목표**:
- ✅ PostgreSQL로 데이터 영구 저장
- ✅ Redis로 캐싱하여 비용 60%+ 절감
- ✅ Database migrations으로 스키마 관리
- ✅ 최적화된 쿼리 작성

**예상 시간**: 40시간 (주당 20시간)

## 왜 데이터베이스와 캐시가 필요한가?

### 현재 문제 (메모리만 사용)

```python
# ❌ 교육용 코드
class CostOptimizer:
    def __init__(self):
        self.cache = {}  # 메모리에만 저장
        self.metrics = []  # 메모리에만 저장

# 문제:
# 1. 재시작 시 모든 데이터 소실
# 2. 캐시 공유 불가 (여러 서버)
# 3. 비용 분석 불가 (히스토리 없음)
# 4. 메모리 부족 위험
```

### 프로덕션 솔루션

```python
# ✅ 프로덕션 코드
class ProductionOptimizer:
    def __init__(self):
        # PostgreSQL: 영구 저장
        self.db = Database(connection_string)

        # Redis: 빠른 캐시
        self.cache = RedisCache(redis_url)

    async def optimize(self, query, context):
        # 1. 캐시 확인
        cache_key = self._get_cache_key(query, context)
        cached = await self.cache.get(cache_key)

        if cached:
            # 2. 캐시 히트 → DB에 기록
            await self.db.log_cache_hit(cache_key)
            return cached

        # 3. 캐시 미스 → 계산
        result = await self._calculate(query, context)

        # 4. 캐시에 저장 (TTL 1시간)
        await self.cache.set(cache_key, result, ttl=3600)

        # 5. DB에 쿼리 로그 저장
        await self.db.log_query(
            query=query,
            tokens=result['tokens'],
            cost=result['cost'],
            cached=False
        )

        return result
```

**효과**:
- 캐시 히트율 60% → **비용 60% 절감**
- 히스토리 추적 가능
- 다중 서버 간 캐시 공유
- 비용 분석 및 예측

## Day 1-3: PostgreSQL & SQLAlchemy (20시간)

### 학습 목표
관계형 데이터베이스로 데이터를 영구 저장합니다.

### 이론 (3시간)

#### SQLAlchemy ORM

**ORM (Object-Relational Mapping)**:
Python 객체 ↔ Database Table

```python
# Raw SQL (힘듦)
cursor.execute("""
    INSERT INTO query_logs (query, tokens, cost, created_at)
    VALUES (%s, %s, %s, %s)
""", (query, tokens, cost, datetime.now()))

# SQLAlchemy ORM (쉬움)
log = QueryLog(
    query=query,
    tokens=tokens,
    cost=cost
)
session.add(log)
session.commit()
```

#### 데이터 모델 설계

```python
# models/database.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class QueryLog(Base):
    """쿼리 실행 로그"""
    __tablename__ = 'query_logs'

    id = Column(Integer, primary_key=True)
    request_id = Column(String(64), unique=True, index=True)
    query = Column(String)
    context_tokens = Column(Integer)
    response_tokens = Column(Integer)
    model = Column(String(50))
    cost = Column(Float)
    latency_ms = Column(Float)
    cached = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class CostMetrics(Base):
    """시간별 비용 집계"""
    __tablename__ = 'cost_metrics'

    id = Column(Integer, primary_key=True)
    hour_timestamp = Column(DateTime, index=True)
    total_queries = Column(Integer)
    total_cost = Column(Float)
    cache_hit_rate = Column(Float)
    avg_latency_ms = Column(Float)


class User(Base):
    """사용자 (API 키 관리용)"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    api_key = Column(String(64), unique=True, index=True)
    quota_limit = Column(Float, default=100.0)  # Monthly $
    quota_used = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 실습 (15시간)

#### Exercise 1: Database Setup (3시간)

**과제**: PostgreSQL 설치 및 연결

```bash
# Docker로 PostgreSQL 실행
docker run --name postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=context_eng \
  -p 5432:5432 \
  -d postgres:15-alpine

# 연결 테스트
psql -h localhost -U postgres -d context_eng
```

```python
# exercises/01_database_setup.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# TODO: 연결 문자열 생성
DATABASE_URL = "postgresql://postgres:password@localhost:5432/context_eng"

# TODO: Engine 생성
engine = create_engine(DATABASE_URL, echo=True)

# TODO: Session 생성
SessionLocal = sessionmaker(bind=engine)

# TODO: 연결 테스트
def test_connection():
    session = SessionLocal()
    try:
        result = session.execute("SELECT version()")
        version = result.fetchone()[0]
        print(f"✓ Connected to PostgreSQL: {version}")
    finally:
        session.close()

if __name__ == "__main__":
    test_connection()
```

**검증**:
```bash
python exercises/01_database_setup.py
# 출력: ✓ Connected to PostgreSQL: PostgreSQL 15.x...
```

#### Exercise 2: Models 정의 (4시간)

**과제**: SQLAlchemy 모델 작성

```python
# exercises/02_models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class QueryLog(Base):
    """TODO: 완성하세요"""
    __tablename__ = 'query_logs'

    # Columns
    id = Column(Integer, primary_key=True)
    # TODO: 필요한 컬럼 추가


class CostMetrics(Base):
    """TODO: 완성하세요"""
    __tablename__ = 'cost_metrics'

    # TODO: 컬럼 정의


class CacheEntry(Base):
    """캐시 메타데이터"""
    __tablename__ = 'cache_entries'

    id = Column(Integer, primary_key=True)
    cache_key = Column(String(255), unique=True, index=True)
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


# 테이블 생성
def create_tables(engine):
    """TODO: 모든 테이블 생성"""
    Base.metadata.create_all(engine)
```

**검증**:
```bash
python exercises/02_models.py

# PostgreSQL에서 확인
psql -h localhost -U postgres -d context_eng
\dt  # 테이블 목록
\d query_logs  # 스키마 확인
```

#### Exercise 3: CRUD Operations (4시간)

**과제**: Create, Read, Update, Delete 구현

```python
# exercises/03_crud_operations.py

from sqlalchemy.orm import Session
from datetime import datetime
from models import QueryLog

def create_query_log(
    session: Session,
    request_id: str,
    query: str,
    tokens: int,
    cost: float,
    model: str
) -> QueryLog:
    """
    TODO: QueryLog 생성

    1. QueryLog 객체 생성
    2. session.add()
    3. session.commit()
    4. 반환
    """
    pass


def get_query_log(session: Session, request_id: str) -> QueryLog:
    """TODO: request_id로 조회"""
    pass


def get_recent_logs(session: Session, limit: int = 10) -> list[QueryLog]:
    """
    TODO: 최근 로그 조회

    힌트:
    - .order_by(QueryLog.created_at.desc())
    - .limit(limit)
    """
    pass


def get_cost_summary(session: Session, start_date: datetime, end_date: datetime) -> dict:
    """
    TODO: 기간별 비용 집계

    힌트:
    - .filter(QueryLog.created_at >= start_date)
    - .filter(QueryLog.created_at <= end_date)
    - func.sum(QueryLog.cost)
    """
    from sqlalchemy import func

    pass


def update_cache_hit_count(session: Session, cache_key: str):
    """TODO: 캐시 히트 카운트 증가"""
    pass


def delete_old_logs(session: Session, days: int = 30):
    """
    TODO: 오래된 로그 삭제

    힌트:
    - datetime.now() - timedelta(days=days)
    - .filter(QueryLog.created_at < cutoff_date)
    - .delete()
    """
    pass


# 테스트
if __name__ == "__main__":
    from database import engine, SessionLocal

    session = SessionLocal()

    # Create
    log = create_query_log(
        session,
        request_id="req_001",
        query="What is context engineering?",
        tokens=1500,
        cost=0.015,
        model="gpt-4-turbo"
    )
    print(f"Created: {log.id}")

    # Read
    retrieved = get_query_log(session, "req_001")
    print(f"Retrieved: {retrieved.query}")

    # List
    recent = get_recent_logs(session, limit=5)
    print(f"Recent logs: {len(recent)}")

    # Aggregate
    summary = get_cost_summary(
        session,
        start_date=datetime(2025, 11, 1),
        end_date=datetime(2025, 11, 30)
    )
    print(f"Cost summary: {summary}")

    session.close()
```

**검증**:
```bash
python exercises/03_crud_operations.py
pytest tests/test_crud.py -v
```

#### Exercise 4: Database Migrations (Alembic) (4시간)

**과제**: Alembic으로 스키마 버전 관리

```bash
# Alembic 설치 및 초기화
pip install alembic
alembic init alembic

# alembic.ini 수정
sqlalchemy.url = postgresql://postgres:password@localhost:5432/context_eng
```

```python
# alembic/env.py 수정

from models import Base  # Import your models

target_metadata = Base.metadata
```

```bash
# 첫 번째 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 히스토리
alembic history

# 롤백
alembic downgrade -1
```

**과제: 스키마 변경 연습**

1. `QueryLog`에 `user_id` 컬럼 추가
2. 마이그레이션 생성
3. 적용
4. 롤백
5. 다시 적용

```python
# models.py 수정
class QueryLog(Base):
    # ...
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="queries")
```

```bash
alembic revision --autogenerate -m "Add user_id to query_logs"
alembic upgrade head
```

### 프로젝트 과제 (Day 1-3): "Persistent Optimizer" (Day 1-3 종료 시)

요구사항:
1. 모든 쿼리를 DB에 로그
2. 시간별 비용 집계
3. 사용자별 quota 관리
4. Database migrations
5. 쿼리 최적화 (인덱스)

```python
# project/persistent_optimizer.py

class PersistentOptimizer:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    async def optimize(self, query: str, context: str, user_id: int) -> dict:
        """
        TODO: 구현

        1. User quota 확인
        2. 최적화 수행
        3. QueryLog 저장
        4. User quota 업데이트
        5. CostMetrics 업데이트
        """
        session = self.Session()

        try:
            # Check quota
            user = session.query(User).get(user_id)
            if user.quota_used >= user.quota_limit:
                raise QuotaExceededError("Monthly quota exceeded")

            # Optimize
            result = self._optimize(query, context)

            # Log
            log = QueryLog(
                query=query,
                user_id=user_id,
                tokens=result['tokens'],
                cost=result['cost'],
                # ...
            )
            session.add(log)

            # Update quota
            user.quota_used += result['cost']

            session.commit()

            return result

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
```

## Day 4-7: Redis Caching (20시간)

### 학습 목표
Redis로 캐싱하여 비용과 지연시간을 대폭 줄입니다.

### 이론 (2시간)

#### 캐싱 전략

**1. Cache-Aside (Lazy Loading)**
```python
def get_data(key):
    # 1. 캐시 확인
    data = cache.get(key)
    if data:
        return data

    # 2. 캐시 미스 → DB 조회
    data = db.query(key)

    # 3. 캐시에 저장
    cache.set(key, data, ttl=3600)

    return data
```

**2. Write-Through**
```python
def save_data(key, value):
    # 1. DB에 저장
    db.save(key, value)

    # 2. 캐시에도 저장
    cache.set(key, value)
```

**3. Write-Behind**
```python
def save_data(key, value):
    # 1. 캐시에만 저장
    cache.set(key, value)

    # 2. 비동기로 DB에 저장
    async_queue.put((key, value))
```

#### TTL (Time To Live)

```python
# 1시간 캐시
cache.set("key", "value", ttl=3600)

# 영구 캐시 (주의!)
cache.set("key", "value")  # Bad!

# 조건부 TTL
ttl = 3600 if is_expensive else 300
cache.set("key", "value", ttl=ttl)
```

### 실습 (16시간)

#### Exercise 5: Redis Setup (2시간)

```bash
# Docker로 Redis 실행
docker run --name redis \
  -p 6379:6379 \
  -d redis:7-alpine

# 연결 테스트
redis-cli ping
# 출력: PONG
```

```python
# exercises/05_redis_setup.py

import redis
import json

# TODO: Redis 클라이언트 생성
client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

# TODO: 연결 테스트
def test_connection():
    client.set('test_key', 'test_value')
    value = client.get('test_key')
    assert value == 'test_value'
    print("✓ Redis connected")

# TODO: 복잡한 객체 저장
def cache_object():
    data = {
        'query': 'test',
        'tokens': 100,
        'cost': 0.001
    }

    # JSON으로 직렬화
    client.set('query:test', json.dumps(data))

    # 역직렬화
    cached = json.loads(client.get('query:test'))
    print(f"Cached: {cached}")
```

#### Exercise 6: Cache Client 구현 (4시간)

```python
# exercises/06_cache_client.py

import redis
import json
import hashlib
from typing import Optional, Any

class RedisCacheClient:
    """프로덕션용 Redis 캐시 클라이언트"""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        TODO: 초기화

        Args:
            redis_url: Redis 연결 URL
            default_ttl: 기본 TTL (초)
        """
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        TODO: 캐시에서 가져오기

        1. client.get(key)
        2. JSON 역직렬화
        3. None이면 None 반환
        """
        pass

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        TODO: 캐시에 저장

        1. JSON 직렬화
        2. client.setex(key, ttl, value)
        """
        pass

    def delete(self, key: str):
        """TODO: 캐시 삭제"""
        pass

    def exists(self, key: str) -> bool:
        """TODO: 키 존재 여부"""
        pass

    def get_ttl(self, key: str) -> int:
        """TODO: 남은 TTL 조회"""
        pass

    def generate_cache_key(self, query: str, context: str, model: str) -> str:
        """
        TODO: 캐시 키 생성

        요구사항:
        - query, context, model 조합의 해시
        - 충돌 최소화 (SHA256)
        - 길이 제한 (Redis key는 짧을수록 좋음)

        힌트:
        hashlib.sha256((query + context + model).encode()).hexdigest()
        """
        pass

    def get_stats(self) -> dict:
        """
        TODO: 캐시 통계

        힌트:
        - client.dbsize(): 총 키 개수
        - client.info('stats'): 통계 정보
        """
        pass


# 테스트
if __name__ == "__main__":
    cache = RedisCacheClient("redis://localhost:6379", default_ttl=300)

    # Set
    cache.set("test", {"value": 123})

    # Get
    value = cache.get("test")
    print(f"Cached value: {value}")

    # TTL
    ttl = cache.get_ttl("test")
    print(f"TTL: {ttl}s")

    # Stats
    stats = cache.get_stats()
    print(f"Stats: {stats}")
```

**검증**:
```bash
python exercises/06_cache_client.py
pytest tests/test_cache_client.py -v
```

#### Exercise 7: Cache Integration (5시간)

**과제**: Optimizer에 캐싱 통합

```python
# exercises/07_cached_optimizer.py

from cache_client import RedisCacheClient
from database import SessionLocal
from models import QueryLog

class CachedOptimizer:
    def __init__(self, redis_url: str, database_url: str):
        self.cache = RedisCacheClient(redis_url)
        self.Session = sessionmaker(bind=create_engine(database_url))

    async def optimize(self, query: str, context: str) -> dict:
        """
        TODO: 캐싱 로직 구현

        Flow:
        1. 캐시 키 생성
        2. 캐시 조회
        3. 히트 → 로그 & 반환
        4. 미스 → 계산 → 캐시 저장 → 로그 & 반환
        """

        # 1. 캐시 키 생성
        cache_key = self.cache.generate_cache_key(query, context, "gpt-4-turbo")

        # 2. 캐시 조회
        cached = self.cache.get(cache_key)

        session = self.Session()

        if cached:
            # 3. 캐시 히트
            self._log_query(session, query, cached, cached=True)
            return cached

        # 4. 캐시 미스 → 계산
        result = self._calculate(query, context)

        # 5. 캐시 저장
        self.cache.set(cache_key, result, ttl=3600)

        # 6. 로그
        self._log_query(session, query, result, cached=False)

        session.close()

        return result

    def _calculate(self, query: str, context: str) -> dict:
        """TODO: 실제 계산 (expensive)"""
        # Call LLM API
        pass

    def _log_query(self, session, query: str, result: dict, cached: bool):
        """TODO: DB에 로그"""
        log = QueryLog(
            query=query,
            tokens=result['tokens'],
            cost=result['cost'],
            cached=cached
        )
        session.add(log)
        session.commit()

    def get_cache_stats(self) -> dict:
        """
        TODO: 캐시 통계

        Returns:
            {
                'total_keys': int,
                'hit_rate': float,
                'memory_used': str
            }
        """
        session = self.Session()

        # DB에서 캐시 히트율 계산
        total = session.query(QueryLog).count()
        cached = session.query(QueryLog).filter_by(cached=True).count()

        hit_rate = cached / total if total > 0 else 0

        session.close()

        return {
            'total_keys': self.cache.client.dbsize(),
            'hit_rate': hit_rate,
            'memory_used': self.cache.client.info('memory')['used_memory_human']
        }
```

**검증**:
```bash
python exercises/07_cached_optimizer.py

# 캐시 효과 측정
for i in range(100):
    # 같은 쿼리 반복
    optimizer.optimize("test query", "test context")

stats = optimizer.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']*100:.1f}%")
# 예상: 99% (첫 번째만 미스)
```

#### Exercise 8: Cache Invalidation (3시간)

**과제**: 캐시 무효화 전략

```python
# exercises/08_cache_invalidation.py

class SmartCacheClient(RedisCacheClient):

    def invalidate_pattern(self, pattern: str):
        """
        TODO: 패턴 매칭으로 캐시 삭제

        예: query:user123:* → 특정 사용자의 모든 캐시 삭제

        힌트:
        - client.keys(pattern)
        - client.delete(*keys)
        """
        pass

    def invalidate_user_cache(self, user_id: int):
        """TODO: 사용자별 캐시 삭제"""
        pattern = f"query:user{user_id}:*"
        self.invalidate_pattern(pattern)

    def invalidate_old_caches(self, days: int = 7):
        """
        TODO: 오래된 캐시 삭제

        방법 1: TTL로 자동 만료 (권장)
        방법 2: 수동 삭제
        """
        pass

    def warm_cache(self, popular_queries: list[tuple[str, str]]):
        """
        TODO: 캐시 워밍 (인기 쿼리 미리 캐싱)

        Args:
            popular_queries: [(query, context), ...]
        """
        for query, context in popular_queries:
            if not self.exists(self.generate_cache_key(query, context, "gpt-4-turbo")):
                # Calculate and cache
                result = calculate(query, context)
                self.set(
                    self.generate_cache_key(query, context, "gpt-4-turbo"),
                    result
                )
```

### 프로젝트 과제 (Day 4-7): "High-Performance Optimizer"

요구사항:
1. Redis 캐싱 (60%+ 히트율 목표)
2. PostgreSQL 영구 저장
3. 캐시 통계 모니터링
4. 캐시 무효화 전략
5. 성능 테스트

```python
# project/high_performance_optimizer.py

class HighPerformanceOptimizer:
    """
    캐싱과 DB를 통합한 고성능 optimizer

    Features:
    - Redis caching (60%+ hit rate)
    - PostgreSQL persistence
    - Cache warming
    - Monitoring
    """

    def __init__(self, redis_url: str, database_url: str):
        self.cache = SmartCacheClient(redis_url)
        self.db = Database(database_url)

    async def optimize(self, query: str, context: str, user_id: int) -> dict:
        # Full implementation
        pass

    def get_performance_stats(self) -> dict:
        """
        성능 통계

        Returns:
            {
                'cache_hit_rate': float,
                'avg_latency_cached': float,
                'avg_latency_uncached': float,
                'cost_savings': float
            }
        """
        pass
```

**검증**:
```bash
# 성능 테스트
pytest tests/test_performance.py -v

# 부하 테스트
locust -f load_test.py --headless -u 100 -r 10 -t 60s

# 결과 확인
cache_hit_rate > 60%
p95_latency_cached < 10ms
p95_latency_uncached < 500ms
```

## Week 3-4 종합 평가

### 체크리스트

#### Database
- [ ] PostgreSQL 설치 및 연결
- [ ] SQLAlchemy 모델 정의
- [ ] CRUD operations 구현
- [ ] Database migrations (Alembic)
- [ ] 쿼리 최적화 (인덱스)

#### Caching
- [ ] Redis 설치 및 연결
- [ ] Cache client 구현
- [ ] Cache-aside 패턴
- [ ] TTL 설정
- [ ] 캐시 무효화 전략
- [ ] 캐시 워밍

#### Performance
- [ ] 60%+ 캐시 히트율
- [ ] 캐시 히트 시 <10ms
- [ ] 메모리 사용 모니터링
- [ ] 비용 60%+ 절감

### 최종 프로젝트

**"Production Data Layer v2.0"**

완성해야 할 것:
- PostgreSQL 스키마
- Redis 캐싱
- 성능 모니터링
- 자동 테스트

**평가 기준**:
- [ ] 모든 데이터 영구 저장
- [ ] 캐시 히트율 60%+
- [ ] 성능 테스트 통과
- [ ] 문서화 완료

### 다음 단계

✅ Week 3-4 완료 시:
- 데이터 영구 저장 ✅
- 60%+ 비용 절감 ✅
- 고성능 시스템 ✅

📚 **[Week 5-6: API Server로 →](../week-05-06-api-server/README.md)**

---

**💡 학습 팁**:
- 인덱스는 처음부터 고려하세요
- 캐시 TTL은 신중하게 설정하세요
- 성능은 측정해야 개선됩니다
- 캐시 무효화는 어렵습니다 - 단순하게 유지하세요

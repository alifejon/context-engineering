# 토큰 경제학 (Token Economics)

## 개요

토큰 경제학은 LLM 애플리케이션의 비용을 이해하고 최적화하는 분야입니다. 프로덕션 환경에서 Context Engineering을 성공적으로 적용하려면 토큰 비용을 정확히 이해하고 관리해야 합니다.

## LLM 비용 구조 이해

### 기본 가격 모델

```python
# 일반적인 LLM 비용 구조
cost = (input_tokens * input_price_per_1k / 1000) + \
       (output_tokens * output_price_per_1k / 1000)

# 예시: GPT-4
input_tokens = 5000
output_tokens = 500

cost = (5000 * 0.03 / 1000) + (500 * 0.06 / 1000)
     = 0.15 + 0.03
     = $0.18
```

### 주요 모델 비용 비교 (2024년 기준)

| Model | Input ($/1K) | Output ($/1K) | Context | 특징 |
|-------|-------------|---------------|---------|------|
| **GPT-3.5 Turbo** | $0.0015 | $0.002 | 16K | 가장 저렴 |
| **GPT-4** | $0.03 | $0.06 | 8K | 높은 품질 |
| **GPT-4 Turbo** | $0.01 | $0.03 | 128K | 균형잡힌 |
| **Claude 3 Haiku** | $0.00025 | $0.00125 | 200K | 초저비용 |
| **Claude 3 Sonnet** | $0.003 | $0.015 | 200K | 중간 비용 |
| **Claude 3 Opus** | $0.015 | $0.075 | 200K | 최고 품질 |
| **Gemini 1.5 Flash** | $0.00035 | $0.0014 | 1M | 매우 저렴 |
| **Gemini 1.5 Pro** | $0.00125 | $0.005 | 1M | 장문 처리 |

### 실제 비용 예시

#### 시나리오 1: 고객 지원 챗봇

```python
# 일반적인 대화
system_prompt = 200 tokens
conversation_history = 800 tokens  # 4턴 대화
user_query = 50 tokens
retrieved_context = 2000 tokens
-----------------
total_input = 3050 tokens

llm_response = 300 tokens
-----------------
total_output = 300 tokens

# GPT-4 비용
cost_per_interaction = (3050 * 0.03 / 1000) + (300 * 0.06 / 1000)
                     = $0.0915 + $0.018
                     = $0.1095 ≈ $0.11

# 월 10만 대화 시
monthly_cost = 100000 * 0.11 = $11,000

# Claude 3 Sonnet으로 변경 시
cost_per_interaction = (3050 * 0.003 / 1000) + (300 * 0.015 / 1000)
                     = $0.00915 + $0.0045
                     = $0.01365 ≈ $0.014

monthly_cost = 100000 * 0.014 = $1,400
# 절감액: $9,600 (87.3% 절감!)
```

#### 시나리오 2: 문서 QA 시스템

```python
# RAG 기반 문서 QA
system_prompt = 300 tokens
user_query = 100 tokens
retrieved_docs = 8000 tokens  # 10개 문서 × 800 tokens
-----------------
total_input = 8400 tokens

llm_response = 500 tokens
-----------------

# GPT-4 Turbo 비용
cost_per_query = (8400 * 0.01 / 1000) + (500 * 0.03 / 1000)
               = $0.084 + $0.015
               = $0.099

# Context Engineering 적용 후 (압축)
retrieved_docs_compressed = 3000 tokens  # 62.5% 압축
total_input_optimized = 3400 tokens

cost_per_query_optimized = (3400 * 0.01 / 1000) + (500 * 0.03 / 1000)
                         = $0.034 + $0.015
                         = $0.049

# 일 1만 쿼리 시
daily_cost_before = 10000 * 0.099 = $990
daily_cost_after = 10000 * 0.049 = $490
daily_savings = $500

# 월간 절감액
monthly_savings = 500 * 30 = $15,000
```

## 비용 최적화 전략

### 전략 1: 모델 선택 최적화

```python
class ModelRouter:
    """작업 복잡도에 따른 모델 라우팅"""

    def __init__(self):
        self.models = {
            "simple": {
                "name": "gpt-3.5-turbo",
                "input_cost": 0.0015,
                "output_cost": 0.002
            },
            "medium": {
                "name": "gpt-4-turbo",
                "input_cost": 0.01,
                "output_cost": 0.03
            },
            "complex": {
                "name": "gpt-4",
                "input_cost": 0.03,
                "output_cost": 0.06
            }
        }

    def route_query(self, query: str, context: str) -> dict:
        """쿼리 복잡도에 따라 모델 선택"""
        complexity = self.assess_complexity(query, context)
        return self.models[complexity]

    def assess_complexity(self, query: str, context: str) -> str:
        """복잡도 평가"""
        # 간단한 휴리스틱
        factors = {
            "query_length": len(query.split()),
            "context_length": len(context.split()),
            "requires_reasoning": self.check_reasoning_required(query),
            "domain_specific": self.check_domain_specific(query)
        }

        score = 0
        if factors["query_length"] > 20:
            score += 1
        if factors["context_length"] > 1000:
            score += 1
        if factors["requires_reasoning"]:
            score += 2
        if factors["domain_specific"]:
            score += 1

        if score <= 1:
            return "simple"
        elif score <= 3:
            return "medium"
        else:
            return "complex"

    def check_reasoning_required(self, query: str) -> bool:
        """추론 필요 여부 확인"""
        reasoning_keywords = [
            "why", "how", "compare", "analyze", "explain",
            "왜", "어떻게", "비교", "분석", "설명"
        ]
        return any(kw in query.lower() for kw in reasoning_keywords)

    def check_domain_specific(self, query: str) -> bool:
        """전문 도메인 여부 확인"""
        # 실제로는 더 정교한 분류기 사용
        return False

# 사용 예시
router = ModelRouter()

queries = [
    "안녕하세요",  # simple → GPT-3.5
    "이 제품의 환불 정책이 어떻게 되나요?",  # simple → GPT-3.5
    "이 두 제품을 비교해서 각각의 장단점을 알려주세요",  # medium → GPT-4 Turbo
    "복잡한 금융 상품 구조를 분석하고 리스크를 평가해주세요"  # complex → GPT-4
]

for query in queries:
    model = router.route_query(query, context="")
    print(f"Query: {query[:50]}... → {model['name']}")
```

**비용 절감 효과:**
```python
# 모든 쿼리에 GPT-4 사용 시
all_gpt4_cost = 10000 * 0.11 = $1,100/day

# 라우팅 적용 시 (분포: 50% simple, 30% medium, 20% complex)
simple_cost = 5000 * 0.01 = $50
medium_cost = 3000 * 0.05 = $150
complex_cost = 2000 * 0.11 = $220
total_routed_cost = $420/day

savings = $1,100 - $420 = $680/day (61.8% 절감)
```

### 전략 2: 컨텍스트 압축

```python
def calculate_compression_roi(
    original_tokens: int,
    compressed_tokens: int,
    quality_retention: float,  # 0.0 ~ 1.0
    input_cost_per_1k: float,
    queries_per_month: int
) -> dict:
    """압축 ROI 계산"""

    # 비용 절감
    token_reduction = original_tokens - compressed_tokens
    cost_saving_per_query = (token_reduction * input_cost_per_1k) / 1000
    monthly_savings = cost_saving_per_query * queries_per_month

    # 품질 손실 비용 (추정)
    # 품질 10% 감소 시 약 5%의 재처리 발생 가정
    quality_loss = 1.0 - quality_retention
    reprocessing_rate = quality_loss * 0.5
    reprocessing_cost = monthly_savings * reprocessing_rate * 2  # 재처리는 2배 비용

    # 순 절감액
    net_savings = monthly_savings - reprocessing_cost

    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "compression_ratio": f"{(1 - compressed_tokens/original_tokens) * 100:.1f}%",
        "quality_retention": f"{quality_retention * 100:.1f}%",
        "monthly_savings": f"${monthly_savings:,.2f}",
        "reprocessing_cost": f"${reprocessing_cost:,.2f}",
        "net_savings": f"${net_savings:,.2f}",
        "roi": f"{(net_savings / monthly_savings) * 100:.1f}%" if monthly_savings > 0 else "N/A"
    }

# 예시: 요약 기반 압축
result = calculate_compression_roi(
    original_tokens=8000,
    compressed_tokens=3000,
    quality_retention=0.92,  # 92% 품질 유지
    input_cost_per_1k=0.01,  # GPT-4 Turbo
    queries_per_month=100000
)

print(result)
# {
#     'compression_ratio': '62.5%',
#     'quality_retention': '92.0%',
#     'monthly_savings': '$5,000.00',
#     'reprocessing_cost': '$400.00',
#     'net_savings': '$4,600.00',
#     'roi': '92.0%'
# }
```

### 전략 3: 캐싱 활용

```python
import hashlib
from datetime import datetime, timedelta

class ContextCache:
    """컨텍스트 캐싱으로 비용 절감"""

    def __init__(self, ttl_minutes: int = 60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.stats = {"hits": 0, "misses": 0, "savings": 0.0}

    def get_cache_key(self, context: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(context.encode()).hexdigest()

    def get(self, context: str) -> tuple[bool, any]:
        """캐시에서 조회"""
        key = self.get_cache_key(context)

        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["timestamp"] < self.ttl:
                self.stats["hits"] += 1
                return True, entry["response"]
            else:
                del self.cache[key]  # 만료된 항목 삭제

        self.stats["misses"] += 1
        return False, None

    def set(self, context: str, response: str, cost: float):
        """캐시에 저장"""
        key = self.get_cache_key(context)
        self.cache[key] = {
            "response": response,
            "timestamp": datetime.now(),
            "cost": cost
        }

    def record_saving(self, cost: float):
        """절감액 기록"""
        self.stats["savings"] += cost

    def get_stats(self) -> dict:
        """통계 조회"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_rate": f"{hit_rate * 100:.1f}%",
            "total_savings": f"${self.stats['savings']:.2f}"
        }

# 사용 예시
cache = ContextCache(ttl_minutes=30)

def query_with_cache(query: str, context: str, cost_per_query: float) -> str:
    """캐시를 활용한 쿼리 처리"""
    # 동일한 컨텍스트가 있는지 확인
    hit, cached_response = cache.get(context)

    if hit:
        cache.record_saving(cost_per_query)
        return cached_response

    # 캐시 미스 - LLM 호출
    response = call_llm(query, context)
    cache.set(context, response, cost_per_query)

    return response

# 반복적인 질문이 많은 경우
# 예: FAQ, 일반적인 문의
common_contexts = [
    "환불 정책 문서",
    "배송 정보",
    "회원 가입 절차"
]

# 캐시 히트율이 40%라면
# 월 10만 쿼리, 쿼리당 $0.05
# 절감액: 100,000 * 0.4 * 0.05 = $2,000/월
```

### 전략 4: 배치 처리

```python
class BatchProcessor:
    """배치 처리로 비용 최적화"""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size

    def process_batch(self, queries: list[dict]) -> list[dict]:
        """여러 쿼리를 하나의 프롬프트로 처리"""
        # 단일 컨텍스트로 통합
        combined_context = self.merge_contexts([q["context"] for q in queries])

        # 여러 질문을 하나로 결합
        combined_query = self.merge_queries([q["query"] for q in queries])

        # 한 번의 LLM 호출로 처리
        response = self.call_llm_batch(combined_query, combined_context)

        # 응답 분리
        return self.split_responses(response, len(queries))

    def merge_contexts(self, contexts: list[str]) -> str:
        """중복 제거하여 컨텍스트 병합"""
        # 중복 문단 제거
        unique_paragraphs = []
        seen = set()

        for context in contexts:
            for paragraph in context.split("\n\n"):
                para_hash = hash(paragraph)
                if para_hash not in seen:
                    unique_paragraphs.append(paragraph)
                    seen.add(para_hash)

        return "\n\n".join(unique_paragraphs)

    def merge_queries(self, queries: list[str]) -> str:
        """쿼리를 번호 매겨 병합"""
        return "\n".join([
            f"{i+1}. {query}"
            for i, query in enumerate(queries)
        ])

# 비용 비교
# 개별 처리:
individual_cost = 10 * 3000 * 0.01 / 1000 = $0.30

# 배치 처리 (50% 컨텍스트 중복 가정):
batch_context = 3000 * 0.5 * 10 = 15000 tokens
batch_queries = 100 * 10 = 1000 tokens
batch_cost = (15000 + 1000) * 0.01 / 1000 = $0.16

savings = $0.30 - $0.16 = $0.14 (46.7% 절감)
```

### 전략 5: 단계적 처리 (Staged Processing)

```python
class StagedProcessor:
    """단계적 처리로 불필요한 비용 방지"""

    def process_query(self, query: str, full_context: str) -> str:
        """단계적으로 처리하여 비용 절감"""

        # Stage 1: 빠른 필터링 (저비용 모델)
        is_relevant = self.quick_check(query, full_context)
        if not is_relevant:
            return "질문이 제공된 컨텍스트와 관련이 없습니다."

        # Stage 2: 컨텍스트 압축
        compressed_context = self.compress_context(full_context, query)

        # Stage 3: 의도 파악 (중간 모델)
        intent = self.classify_intent(query)

        # Stage 4: 적절한 모델로 최종 처리
        if intent == "simple":
            return self.process_simple(query, compressed_context)
        elif intent == "complex":
            return self.process_complex(query, compressed_context)

    def quick_check(self, query: str, context: str) -> bool:
        """GPT-3.5로 빠른 관련성 체크"""
        prompt = f"Is this query relevant to the context? Answer yes or no.\nQuery: {query}"
        response = call_gpt35(prompt)  # 저비용
        return "yes" in response.lower()

# 비용 분석
# 100 쿼리 중 20%만 관련성 있는 경우

# Without staged processing:
cost_all = 100 * 0.10 = $10.00

# With staged processing:
stage1_cost = 100 * 0.001 = $0.10  # GPT-3.5로 필터링
stage2_cost = 20 * 0.10 = $2.00    # 관련 쿼리만 GPT-4로 처리
total_staged = $2.10

savings = $10.00 - $2.10 = $7.90 (79% 절감)
```

## 비용 모니터링 및 분석

```python
class CostTracker:
    """비용 추적 및 분석"""

    def __init__(self):
        self.logs = []

    def log_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        query_type: str = None,
        user_id: str = None
    ):
        """요청 로깅"""
        self.logs.append({
            "timestamp": datetime.now(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "query_type": query_type,
            "user_id": user_id
        })

    def get_daily_summary(self, date: datetime = None) -> dict:
        """일일 비용 요약"""
        if date is None:
            date = datetime.now()

        day_logs = [
            log for log in self.logs
            if log["timestamp"].date() == date.date()
        ]

        if not day_logs:
            return {}

        total_cost = sum(log["cost"] for log in day_logs)
        total_requests = len(day_logs)
        total_input_tokens = sum(log["input_tokens"] for log in day_logs)
        total_output_tokens = sum(log["output_tokens"] for log in day_logs)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_requests": total_requests,
            "total_cost": f"${total_cost:.2f}",
            "avg_cost_per_request": f"${total_cost/total_requests:.4f}",
            "total_tokens": total_input_tokens + total_output_tokens,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cost_by_model": self._cost_by_model(day_logs)
        }

    def _cost_by_model(self, logs: list) -> dict:
        """모델별 비용 분석"""
        model_costs = {}
        for log in logs:
            model = log["model"]
            if model not in model_costs:
                model_costs[model] = {"cost": 0, "requests": 0}
            model_costs[model]["cost"] += log["cost"]
            model_costs[model]["requests"] += 1

        return {
            model: {
                "total_cost": f"${data['cost']:.2f}",
                "requests": data["requests"],
                "avg_cost": f"${data['cost']/data['requests']:.4f}"
            }
            for model, data in model_costs.items()
        }

    def get_cost_anomalies(self, threshold_multiplier: float = 2.0) -> list:
        """비정상적인 고비용 요청 탐지"""
        if not self.logs:
            return []

        avg_cost = sum(log["cost"] for log in self.logs) / len(self.logs)
        threshold = avg_cost * threshold_multiplier

        anomalies = [
            {
                "timestamp": log["timestamp"],
                "cost": f"${log['cost']:.2f}",
                "input_tokens": log["input_tokens"],
                "output_tokens": log["output_tokens"],
                "model": log["model"],
                "deviation": f"{(log['cost'] / avg_cost):.1f}x average"
            }
            for log in self.logs
            if log["cost"] > threshold
        ]

        return sorted(anomalies, key=lambda x: float(x["cost"][1:]), reverse=True)

    def get_optimization_recommendations(self) -> list:
        """최적화 권장사항"""
        recommendations = []

        # 분석 1: 고비용 모델 과다 사용
        model_usage = {}
        for log in self.logs:
            model_usage[log["model"]] = model_usage.get(log["model"], 0) + 1

        total_requests = len(self.logs)
        gpt4_usage = model_usage.get("gpt-4", 0) / total_requests if total_requests > 0 else 0

        if gpt4_usage > 0.5:
            recommendations.append({
                "priority": "high",
                "issue": "GPT-4 과다 사용",
                "current": f"{gpt4_usage*100:.1f}% of requests",
                "recommendation": "간단한 쿼리는 GPT-3.5나 Claude Haiku 사용 고려",
                "potential_savings": "up to 60-80%"
            })

        # 분석 2: 평균 입력 토큰 수
        avg_input = sum(log["input_tokens"] for log in self.logs) / len(self.logs)
        if avg_input > 4000:
            recommendations.append({
                "priority": "medium",
                "issue": "높은 평균 입력 토큰",
                "current": f"{avg_input:.0f} tokens per request",
                "recommendation": "컨텍스트 압축 또는 요약 적용",
                "potential_savings": "30-50%"
            })

        # 분석 3: 캐시 미사용 (반복 컨텍스트)
        # 간단한 휴리스틱: 동일한 입력 토큰 수가 자주 반복되면 캐싱 기회
        token_counts = [log["input_tokens"] for log in self.logs]
        from collections import Counter
        common_counts = Counter(token_counts).most_common(5)
        repetition_rate = sum(count for _, count in common_counts) / len(token_counts)

        if repetition_rate > 0.3:
            recommendations.append({
                "priority": "high",
                "issue": "반복적인 쿼리 패턴 감지",
                "current": f"{repetition_rate*100:.1f}% repetition rate",
                "recommendation": "응답 캐싱 구현",
                "potential_savings": "20-40%"
            })

        return recommendations

# 사용 예시
tracker = CostTracker()

# 요청 로깅
tracker.log_request(
    model="gpt-4",
    input_tokens=5000,
    output_tokens=500,
    cost=0.18,
    query_type="document_qa"
)

# 일일 요약
summary = tracker.get_daily_summary()
print(summary)

# 비정상 요청 탐지
anomalies = tracker.get_cost_anomalies(threshold_multiplier=3.0)
print("High-cost requests:", anomalies)

# 최적화 권장사항
recommendations = tracker.get_optimization_recommendations()
for rec in recommendations:
    print(f"[{rec['priority'].upper()}] {rec['issue']}")
    print(f"  → {rec['recommendation']}")
    print(f"  → Potential savings: {rec['potential_savings']}")
```

## 실전 비용 최적화 체크리스트

### 1. 모델 선택
- [ ] 작업 복잡도에 맞는 모델 사용
- [ ] 간단한 작업은 저비용 모델로 라우팅
- [ ] 정기적으로 새로운 모델의 가격/성능 비교

### 2. 컨텍스트 최적화
- [ ] 불필요한 컨텍스트 제거
- [ ] 중복 정보 제거
- [ ] 컨텍스트 압축 적용
- [ ] 우선순위 기반 컨텍스트 선택

### 3. 캐싱
- [ ] 반복적인 쿼리 패턴 식별
- [ ] 캐싱 전략 구현
- [ ] 캐시 히트율 모니터링

### 4. 배치 처리
- [ ] 배치 가능한 작업 식별
- [ ] 컨텍스트 중복 최소화
- [ ] 배치 크기 최적화

### 5. 모니터링
- [ ] 모든 요청 비용 로깅
- [ ] 일일/주간/월간 리포트
- [ ] 비정상 비용 알림 설정
- [ ] ROI 추적

## 비용 최적화 의사결정 트리

```
쿼리 받음
├─ 캐시에 있는가?
│  └─ YES → 캐시 반환 (비용: $0)
│
├─ 간단한 쿼리인가?
│  └─ YES → GPT-3.5 사용 ($$$)
│
├─ 배치 가능한가?
│  └─ YES → 배치 처리 대기열 추가 ($$)
│
├─ 컨텍스트가 큰가? (>5K tokens)
│  ├─ YES → 압축 적용 후 처리 ($$$)
│  └─ NO → 그대로 처리 ($$$$)
│
└─ GPT-4 필요한가?
   ├─ YES → GPT-4 사용 ($$$$$)
   └─ NO → GPT-4 Turbo 사용 ($$$$)
```

## 다음 단계

- [컨텍스트 압축](../02-core-concepts/context-compression.md) - 실전 압축 기법
- [비용 최적화 예제](../../examples/05-production-patterns/cost-optimization/) - 구현 예제

## 요약

1. **정확한 비용 추적**: 모든 요청의 토큰 수와 비용 로깅
2. **적절한 모델 선택**: 작업에 맞는 모델 사용
3. **컨텍스트 최적화**: 불필요한 토큰 제거 및 압축
4. **캐싱 활용**: 반복 쿼리 비용 절감
5. **지속적 모니터링**: 비용 추이 분석 및 최적화

**핵심 인사이트**: Context Engineering을 통한 비용 최적화는 일회성이 아닌 지속적인 프로세스입니다. 정기적인 모니터링과 분석을 통해 개선 기회를 찾아야 합니다.

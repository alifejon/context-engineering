# 성능 최적화 가이드

## 측정 지표

### 1. 지연 시간 (Latency)
```python
import time

def measure_latency(fn):
    start = time.time()
    result = fn()
    latency = time.time() - start
    return result, latency

# 목표: < 2초 (대부분의 쿼리)
```

### 2. 비용 (Cost)
```python
def calculate_cost(input_tokens: int, output_tokens: int, model: str):
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
    }
    price = pricing[model]
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1000

# 목표: 쿼리당 $0.05 미만 (일반적인 케이스)
```

### 3. 처리량 (Throughput)
```python
# 목표: 분당 100+ 쿼리 처리
```

## 최적화 전략

### 1. 컨텍스트 크기 최적화
```python
# Before: 평균 8000 tokens
# After: 평균 3000 tokens (62.5% 감소)
# 결과: 비용 62.5% 절감, 응답 속도 40% 향상
```

### 2. 캐싱 활용
```python
# 캐시 히트율 40% 달성 시
# 비용 절감: 40%
# 응답 시간: 90% 감소 (즉시 응답)
```

### 3. 모델 라우팅
```python
# 간단한 쿼리 50% → GPT-3.5 (20배 저렴)
# 비용 절감: 약 45%
```

### 4. 배치 처리
```python
# 10개 쿼리 개별 처리: 10초, $0.50
# 10개 쿼리 배치 처리: 3초, $0.20
# 개선: 70% 빠름, 60% 저렴
```

## 벤치마크 예시

```python
# 최적화 전
- 평균 응답 시간: 5.2초
- 평균 비용: $0.12/쿼리
- 처리량: 30 qps

# 최적화 후
- 평균 응답 시간: 1.8초 (65% 개선)
- 평균 비용: $0.03/쿼리 (75% 절감)
- 처리량: 95 qps (217% 향상)
```

## 프로파일링

```python
class ContextProfiler:
    """성능 프로파일링"""

    def profile(self, query: str, documents: list):
        timings = {}

        start = time.time()
        # 검색
        docs = vector_search(query, documents)
        timings["search"] = time.time() - start

        start = time.time()
        # 우선순위화
        prioritized = prioritize(docs, query)
        timings["prioritization"] = time.time() - start

        start = time.time()
        # 압축
        compressed = compress(prioritized)
        timings["compression"] = time.time() - start

        start = time.time()
        # LLM 호출
        response = llm.generate(compressed, query)
        timings["llm_call"] = time.time() - start

        return {
            "timings": timings,
            "total": sum(timings.values()),
            "bottleneck": max(timings, key=timings.get)
        }
```

## 요약
측정 → 병목 식별 → 최적화 → 반복

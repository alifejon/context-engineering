# 컨텍스트 문제 디버깅

## 일반적인 문제들

### 1. 토큰 제한 초과
```python
# 증상: "context_length_exceeded" 에러

# 디버깅
print(f"System: {count_tokens(system_prompt)}")
print(f"Context: {count_tokens(context)}")
print(f"Query: {count_tokens(query)}")
print(f"Total: {count_tokens(system_prompt + context + query)}")
print(f"Max: {model_max_tokens}")

# 해결
context = compress_to_budget(context, budget=available_tokens)
```

### 2. 관련 없는 응답
```python
# 증상: LLM이 엉뚱한 답변

# 디버깅
relevance = measure_relevance(context, query)
print(f"Context relevance: {relevance}")

if relevance < 0.5:
    print("WARNING: Low relevance context")
    print("Context preview:", context[:500])

# 해결
# - 검색 쿼리 개선
# - 리랭킹 추가
# - 필터링 임계값 조정
```

### 3. Lost in the Middle
```python
# 증상: 컨텍스트 중간의 정보 무시

# 디버깅
def test_context_positions(context: str, query: str):
    """컨텍스트 위치별 정보 활용도 테스트"""
    # 중요 정보를 다른 위치에 배치하고 테스트
    positions = ["beginning", "middle", "end"]
    results = {}

    for pos in positions:
        test_context = place_info_at(context, pos)
        response = llm.generate(test_context, query)
        results[pos] = check_info_used(response)

    return results

# 해결: Priority Sandwich 전략 사용
```

### 4. 높은 비용
```python
# 증상: 예상보다 높은 API 비용

# 디버깅
tracker = CostTracker()
daily_report = tracker.get_daily_summary()
print(f"Avg tokens: {daily_report['avg_tokens']}")
print(f"Avg cost: {daily_report['avg_cost']}")

anomalies = tracker.get_cost_anomalies()
for a in anomalies:
    print(f"High cost query: {a['query'][:50]}... (${a['cost']})")

# 해결
# - 압축 강화
# - 모델 라우팅
# - 캐싱 도입
```

## 디버깅 도구

```python
class ContextDebugger:
    """컨텍스트 디버깅 도구"""

    def diagnose(self, context: str, query: str) -> dict:
        """종합 진단"""
        return {
            "token_count": count_tokens(context),
            "relevance_score": measure_relevance(context, query),
            "has_duplicates": self.check_duplicates(context),
            "has_contradictions": self.check_contradictions(context),
            "readability": self.check_readability(context),
            "structure": self.analyze_structure(context)
        }

    def check_duplicates(self, context: str) -> bool:
        """중복 체크"""
        sentences = context.split('.')
        return len(sentences) != len(set(sentences))

    def check_contradictions(self, context: str) -> list:
        """모순 감지 (간단한 버전)"""
        # 실제로는 더 정교한 NLP 필요
        contradictions = []
        # ... 구현
        return contradictions

    def check_readability(self, context: str) -> float:
        """가독성 점수"""
        # ... 구현
        return 0.8

    def analyze_structure(self, context: str) -> dict:
        """구조 분석"""
        return {
            "has_sections": "##" in context,
            "has_lists": "-" in context or "*" in context,
            "paragraph_count": context.count("\n\n"),
        }

# 사용
debugger = ContextDebugger()
diagnosis = debugger.diagnose(context, query)
if diagnosis["relevance_score"] < 0.6:
    print("⚠️ Low relevance! Consider improving context.")
if diagnosis["token_count"] > 8000:
    print("⚠️ Token limit approaching! Consider compression.")
```

## 로깅 및 모니터링

```python
import logging

# 구조화된 로깅
logging.info("context_built", extra={
    "query": query,
    "token_count": count_tokens(context),
    "doc_count": len(documents),
    "relevance": relevance_score,
    "latency_ms": latency * 1000
})

# 알림 설정
if relevance_score < 0.5:
    alert("Low quality context", severity="warning")
if token_count > max_tokens * 0.95:
    alert("Token limit approaching", severity="critical")
```

## 요약

문제 발생 시:
1. **측정**: 토큰, 관련성, 비용 등 측정
2. **진단**: 디버깅 도구로 문제 파악
3. **해결**: 적절한 최적화 적용
4. **검증**: 개선 효과 확인

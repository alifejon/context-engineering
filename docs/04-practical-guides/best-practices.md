# Context Engineering 모범 사례

## 핵심 원칙

### 1. 항상 토큰 예산을 먼저 계산하라
```python
# ❌ 나쁜 예
context = load_all_documents()
prompt = f"{system_prompt}\n{context}\n{query}"

# ✅ 좋은 예
max_tokens = 8000
reserved = 500 + 1000  # system + output
available = max_tokens - reserved
context = select_and_compress(documents, budget=available)
```

### 2. 우선순위화를 항상 적용하라
```python
# ❌ 나쁜 예
docs = vector_search(query, k=10)
context = "\n".join([d.content for d in docs])

# ✅ 좋은 예
docs = vector_search(query, k=20)
prioritized = prioritize_by_relevance(docs, query)
top_docs = prioritized[:10]
context = assemble_with_priority_sandwich(top_docs)
```

### 3. 컨텍스트 품질을 모니터링하라
```python
# ✅ 프로덕션에서 항상
quality = evaluate_context_quality(context, query)
if quality["score"] < 0.7:
    alert("Low context quality detected")
    context = improve_context(context, query)
```

### 4. 캐싱을 적극 활용하라
```python
# ✅ 반복적인 쿼리는 캐싱
cache_key = hash(query + context_signature)
if cache_key in cache:
    return cache[cache_key]

response = llm.generate(query, context)
cache[cache_key] = response
return response
```

### 5. 쿼리 유형에 따라 전략을 다르게 하라
```python
def build_context(query: str, docs: list):
    query_type = classify_query(query)

    if query_type == "factual":
        return factual_context(docs, max_tokens=2000)
    elif query_type == "how_to":
        return tutorial_context(docs, max_tokens=4000)
    elif query_type == "comparison":
        return comparison_context(docs, max_tokens=3000)
```

## 체크리스트

### 개발 시
- [ ] 토큰 카운팅 정확히 구현
- [ ] 압축 전략 선택
- [ ] 우선순위화 로직 구현
- [ ] 에러 핸들링 (토큰 초과 등)
- [ ] 로깅 및 모니터링 추가

### 배포 전
- [ ] 다양한 쿼리 유형으로 테스트
- [ ] 토큰 비용 분석
- [ ] 성능 벤치마크
- [ ] A/B 테스트 준비
- [ ] 알림 시스템 설정

### 운영 중
- [ ] 일일 비용 리포트 확인
- [ ] 품질 메트릭 모니터링
- [ ] 사용자 피드백 수집
- [ ] 정기적인 최적화
- [ ] 새로운 모델/전략 실험

## 일반적인 실수

### ❌ 실수 1: 토큰 제한 무시
```python
# 에러 발생 위험
context = "\n".join(all_documents)
```

### ❌ 실수 2: 압축 없이 모든 검색 결과 사용
```python
# 비효율적
docs = vector_search(query, k=50)
context = "\n".join([d.content for d in docs])
```

### ❌ 실수 3: 정적인 컨텍스트 구조
```python
# 모든 쿼리에 동일한 구조
template = f"System: {system}\nDocs: {docs}\nQuery: {query}"
```

### ❌ 실수 4: 모니터링 없음
```python
# 문제를 발견하지 못함
response = llm.generate(context)
return response  # 품질 체크 없음
```

## 성능 최적화 팁

1. **배치 처리**: 유사한 쿼리는 묶어서 처리
2. **병렬 검색**: 벡터/키워드 검색 동시 실행
3. **사전 계산**: 임베딩, 요약 미리 계산
4. **지연 로딩**: 필요할 때만 컨텍스트 로드
5. **점진적 처리**: 단계적으로 필터링

## 요약

핵심은 **측정, 최적화, 반복**입니다.
- 토큰 사용량 측정
- 품질과 비용 최적화
- 지속적 개선

# Case Study: 문서 QA 시스템 최적화

## 배경

**회사**: 기술 문서 플랫폼 스타트업
**문제**: RAG 기반 문서 QA 시스템의 높은 비용과 느린 응답 속도
**규모**: 월 50만 쿼리, 10,000개 문서

## 초기 상황

### 시스템 구성
```python
# 기본 RAG 구현
def answer_question(question: str):
    # 1. 벡터 검색
    docs = vectorstore.similarity_search(question, k=15)

    # 2. 모든 문서 연결
    context = "\n\n".join([doc.page_content for doc in docs])

    # 3. GPT-4로 답변 생성
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on documents."},
            {"role": "user", "content": f"Context:\n{context}\n\nQ: {question}"}
        ]
    )
    return response.choices[0].message.content
```

### 문제점
- **평균 응답 시간**: 6.5초
- **평균 비용**: $0.28 per query
- **월 비용**: $140,000
- **정확도**: 76%
- **사용자 불만**: 느린 속도, 때로 관련 없는 답변

## Context Engineering 적용

### Phase 1: 분석 및 측정

```python
# 문제 분석
problems = {
    "high_tokens": {
        "average": 12000,
        "max": 25000,
        "cause": "15개 문서 전체 사용"
    },
    "irrelevant_context": {
        "percentage": 40,
        "cause": "단순 유사도 검색, 필터링 없음"
    },
    "no_prioritization": {
        "issue": "모든 문서 동등하게 취급"
    }
}
```

### Phase 2: 우선순위화 구현

```python
class DocumentPrioritizer:
    def prioritize(self, docs: list, query: str) -> list:
        """문서 우선순위화"""
        scored_docs = []

        for doc in docs:
            score = self.calculate_composite_score(doc, query)
            scored_docs.append((doc, score))

        return sorted(scored_docs, key=lambda x: x[1], reverse=True)

    def calculate_composite_score(self, doc, query):
        """복합 점수 계산"""
        relevance = self.relevance_score(doc, query)
        recency = self.recency_score(doc)
        credibility = self.credibility_score(doc)

        return (
            relevance * 0.5 +
            recency * 0.3 +
            credibility * 0.2
        )

# 효과: 상위 5개 문서만으로 정확도 유지
```

### Phase 3: 압축 적용

```python
class ContextCompressor:
    def compress(self, docs: list, query: str, max_tokens: int) -> str:
        """하이브리드 압축"""
        # 1. 우선순위화
        prioritized = self.prioritizer.prioritize(docs, query)

        # 2. 추출형 압축
        extracted = []
        for doc, score in prioritized[:8]:
            important_sentences = self.extract_key_sentences(
                doc.page_content,
                query
            )
            extracted.append(important_sentences)

        combined = "\n\n".join(extracted)

        # 3. 예산 초과 시 생성형 압축
        if count_tokens(combined) > max_tokens:
            combined = self.summarize(combined, target_tokens=max_tokens)

        return combined

# 효과: 12K → 3.5K tokens (70% 감소)
```

### Phase 4: 동적 컨텍스트 구성

```python
class DynamicQASystem:
    def answer(self, question: str):
        # 1. 쿼리 분석
        query_type = self.analyzer.classify(question)
        complexity = self.analyzer.assess_complexity(question)

        # 2. 적응형 검색
        if complexity == "simple":
            k = 5
            max_context_tokens = 2000
        elif complexity == "medium":
            k = 10
            max_context_tokens = 3500
        else:
            k = 15
            max_context_tokens = 5000

        # 3. 검색 및 압축
        docs = self.vectorstore.similarity_search(question, k=k)
        context = self.compressor.compress(docs, question, max_context_tokens)

        # 4. 모델 라우팅
        if complexity == "simple":
            model = "gpt-3.5-turbo"
        else:
            model = "gpt-4"

        # 5. 답변 생성
        return self.generate_answer(question, context, model)

# 효과:
# - Simple 쿼리 (60%): GPT-3.5 사용, 2K tokens
# - Complex 쿼리 (40%): GPT-4 사용, 3.5K tokens
```

### Phase 5: 캐싱 도입

```python
class CachedQASystem:
    def __init__(self):
        self.response_cache = {}
        self.context_cache = {}

    def answer(self, question: str):
        # 1. 응답 캐시 확인
        cache_key = self.get_cache_key(question)
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]

        # 2. 컨텍스트 캐시 확인
        docs = self.get_or_cache_documents(question)

        # 3. 답변 생성 및 캐싱
        answer = self.dynamic_qa.answer(question)
        self.response_cache[cache_key] = answer

        return answer

# 효과: 30% 캐시 히트율 달성
```

## 결과

### 성능 개선

| 메트릭 | Before | After | 개선 |
|--------|--------|-------|------|
| 평균 응답 시간 | 6.5초 | 2.1초 | **67% 개선** |
| 평균 토큰 | 12,000 | 3,500 | **71% 감소** |
| 쿼리당 비용 | $0.28 | $0.07 | **75% 절감** |
| 월 비용 | $140,000 | $35,000 | **$105K 절감** |
| 정확도 | 76% | 87% | **11%p 향상** |
| 사용자 만족도 | 3.2/5 | 4.5/5 | **41% 향상** |

### 세부 개선 사항

#### 1. 비용 절감 분석
```
압축으로 인한 절감: $75,000/월 (70% 토큰 감소)
모델 라우팅: $20,000/월 (60% GPT-3.5 사용)
캐싱: $10,000/월 (30% 캐시 히트)
----------------------------------------------
총 절감: $105,000/월
ROI: 구현 비용 대비 3개월 만에 회수
```

#### 2. 품질 향상 요인
- 관련성 높은 문서 우선 선택: +6%p
- 중복 정보 제거: +3%p
- 쿼리 유형별 최적화: +2%p

#### 3. 속도 향상 요인
- 토큰 감소로 인한 LLM 처리 속도: 40%
- 모델 라우팅 (GPT-3.5 더 빠름): 15%
- 캐싱: 12%

## 교훈

### 성공 요인
1. **측정 먼저**: 정확한 문제 파악이 핵심
2. **단계적 적용**: 한 번에 하나씩 개선
3. **A/B 테스트**: 각 변경사항의 효과 검증
4. **사용자 피드백**: 정량적 + 정성적 평가

### 도전 과제
1. **초기 구현 복잡도**: 2주 개발 기간 필요
2. **모니터링 설정**: 품질 메트릭 정의 및 추적
3. **캐시 무효화**: 문서 업데이트 시 관리

### 다음 단계
- [ ] 멀티모달 지원 (이미지, 다이어그램)
- [ ] 개인화된 컨텍스트 (사용자별)
- [ ] 실시간 학습 (피드백 기반)

## 코드 저장소

전체 구현 코드: [github.com/example/doc-qa-optimization](github.com/example)

## 연락처

이 사례에 대한 질문이나 협업 문의:
- 이메일: team@example.com
- LinkedIn: [회사 페이지]

---

**핵심 메시지**: Context Engineering으로 75% 비용 절감하면서 품질 11% 향상 달성!

# Context Engineering이란?

## 개요

Context Engineering은 LLM(Large Language Model) 애플리케이션에서 컨텍스트 윈도우를 체계적으로 설계, 관리, 최적화하는 엔지니어링 분야입니다.

## 프롬프트 엔지니어링 vs RAG vs Context Engineering

### 진화의 관점에서

```
Phase 1: Prompt Engineering (2020-2021)
"어떻게 질문할 것인가?"
- Few-shot examples
- Instruction tuning
- Chain-of-thought

Phase 2: RAG (2021-2023)
"어떻게 정보를 찾을 것인가?"
- Vector search
- Semantic retrieval
- Document chunking

Phase 3: Context Engineering (2023-현재)
"어떻게 컨텍스트를 관리할 것인가?"
- Context compression
- Dynamic assembly
- Token optimization
```

### 실제 문제로 이해하기

#### 시나리오: 고객 지원 챗봇

**Prompt Engineering 관점:**
```python
prompt = """
당신은 친절한 고객 지원 상담원입니다.
다음 규칙을 따르세요:
1. 정중하게 응대하세요
2. 구체적인 해결책을 제시하세요
3. 필요시 추가 정보를 요청하세요
"""
```
→ "어떻게 물어볼까?"에 집중

**RAG 관점:**
```python
# 사용자 질문으로 관련 문서 검색
query = "환불 정책이 어떻게 되나요?"
relevant_docs = vector_store.similarity_search(query, k=5)
context = "\n".join([doc.page_content for doc in relevant_docs])
```
→ "어떻게 정보를 찾을까?"에 집중

**Context Engineering 관점:**
```python
# 1. 컨텍스트 윈도우 확인
available_tokens = 8000 - len(system_prompt) - len(user_query) - 1000  # 여유분

# 2. 우선순위 기반 컨텍스트 구성
contexts = [
    {"type": "current_conversation", "priority": 1, "tokens": 500},
    {"type": "user_profile", "priority": 2, "tokens": 200},
    {"type": "recent_tickets", "priority": 3, "tokens": 300},
    {"type": "knowledge_base", "priority": 4, "tokens": 2000},
]

# 3. 동적으로 컨텍스트 압축 및 어셈블리
optimized_context = assemble_context(
    contexts,
    max_tokens=available_tokens,
    compression_strategy="semantic"
)
```
→ "어떻게 효율적으로 관리할까?"에 집중

## Context Engineering이 필요한 이유

### 1. 컨텍스트 윈도우의 한계

모든 LLM은 제한된 컨텍스트 윈도우를 가지고 있습니다:

| Model | Context Window | 실제 유효 범위 |
|-------|---------------|--------------|
| GPT-3.5 | 16K tokens | ~12K tokens |
| GPT-4 | 128K tokens | ~100K tokens |
| Claude 3 | 200K tokens | ~180K tokens |
| Gemini 1.5 | 1M tokens | ~800K tokens |

**문제점:**
- RAG로 검색한 100개 문서를 모두 넣을 수 없음
- 멀티턴 대화 시 이전 대화 내역이 쌓임
- 시스템 프롬프트, 예제, 도구 정의 등도 토큰 소비

### 2. Lost in the Middle 문제

```
컨텍스트 시작: 정보 A [중요, 잘 참조됨]
   ↓
컨텍스트 중간: 정보 B, C, D [중요하지만 무시됨 ❌]
   ↓
컨텍스트 끝: 정보 E [중요, 잘 참조됨]
```

**연구 결과:**
- LLM은 컨텍스트 시작과 끝 부분을 더 잘 활용
- 중간 부분의 정보는 종종 무시됨
- 단순히 정보를 많이 넣는다고 좋은 것이 아님

**Context Engineering 해결책:**
```python
# 중요한 정보를 전략적으로 배치
context = f"""
{most_relevant_info}  # 시작 부분

{system_instructions}  # 중간 부분은 구조화된 정보

{query_specific_context}  # 끝 부분
"""
```

### 3. 비용 최적화

**토큰 비용 예시 (GPT-4):**
- Input: $0.03 / 1K tokens
- Output: $0.06 / 1K tokens

```python
# 비효율적인 방식
context = load_all_documents()  # 50K tokens
cost_per_request = 50 * 0.03 = $1.50

# Context Engineering 적용
optimized_context = compress_and_prioritize(documents)  # 5K tokens
cost_per_request = 5 * 0.03 = $0.15

# 월 10만 요청 시
# Before: $150,000
# After: $15,000
# 절감: $135,000 (90%)
```

### 4. 응답 품질 향상

**실험 결과:**

| 방식 | 컨텍스트 크기 | 정확도 | 응답 시간 |
|------|--------------|--------|----------|
| 무압축 (모든 문서) | 40K tokens | 73% | 8.2s |
| 단순 절단 | 8K tokens | 68% | 2.1s |
| Context Engineering | 8K tokens | 87% | 2.3s |

**이유:**
- 관련성 높은 정보만 포함
- 노이즈 제거
- 구조화된 컨텍스트

## Context Engineering의 핵심 구성 요소

### 1. Context Planning (계획)
```python
# 어떤 컨텍스트가 필요한가?
required_contexts = analyze_query(user_query)
# → ["product_info", "pricing", "user_history"]
```

### 2. Context Retrieval (검색)
```python
# RAG를 통한 정보 검색
raw_contexts = retrieve_relevant_contexts(required_contexts)
```

### 3. Context Optimization (최적화)
```python
# 압축, 우선순위화, 필터링
optimized = optimize_contexts(
    raw_contexts,
    max_tokens=target_token_count,
    strategies=["summarize", "filter", "rerank"]
)
```

### 4. Context Assembly (조합)
```python
# 효과적인 순서로 컨텍스트 구성
final_context = assemble_contexts(
    optimized,
    template=context_template,
    placement_strategy="priority_based"
)
```

### 5. Context Monitoring (모니터링)
```python
# 컨텍스트 품질 추적
metrics = monitor_context_quality(
    context=final_context,
    response=llm_response,
    user_feedback=feedback
)
```

## 실전 예시: 문서 QA 시스템

### Before (RAG만 사용)

```python
def answer_question(question: str):
    # 단순히 상위 10개 문서 검색
    docs = vector_store.similarity_search(question, k=10)
    context = "\n\n".join([doc.content for doc in docs])

    # 프롬프트에 그대로 추가
    prompt = f"Context: {context}\n\nQuestion: {question}"
    return llm.generate(prompt)

# 문제점:
# - 10개 문서가 너무 많을 수 있음 (토큰 초과)
# - 중복 정보 포함
# - 관련 없는 정보도 포함될 수 있음
# - Lost in the middle 문제
```

### After (Context Engineering 적용)

```python
def answer_question(question: str):
    # 1. 쿼리 분석
    query_type = analyze_query_type(question)
    required_token_budget = calculate_token_budget(question)

    # 2. 다단계 검색
    initial_docs = vector_store.similarity_search(question, k=20)

    # 3. 리랭킹 및 필터링
    reranked_docs = rerank_by_relevance(question, initial_docs)
    filtered_docs = filter_by_threshold(reranked_docs, threshold=0.7)

    # 4. 중복 제거 및 압축
    deduplicated = remove_duplicate_info(filtered_docs)
    compressed = compress_contexts(
        deduplicated,
        target_tokens=required_token_budget,
        method="extractive_summary"
    )

    # 5. 전략적 배치
    context = assemble_strategic_context(
        compressed,
        query_type=query_type,
        placement="most_relevant_first_and_last"
    )

    # 6. 메타데이터 추가
    context_with_meta = add_metadata(
        context,
        doc_sources=filtered_docs,
        relevance_scores=True
    )

    return llm.generate(f"Context: {context_with_meta}\n\nQuestion: {question}")

# 개선점:
# ✅ 토큰 예산 관리
# ✅ 높은 품질의 컨텍스트
# ✅ 중복 제거
# ✅ 전략적 배치
# ✅ 비용 최적화
```

## Context Engineering vs 기존 접근법 비교

### 의사 결정 트리

```
질문을 받았을 때:

├─ 단순한 일회성 질문?
│  └─ YES → Prompt Engineering만으로 충분
│
├─ 외부 지식이 필요한가?
│  └─ YES → RAG 필요
│     │
│     ├─ 검색 결과가 컨텍스트 윈도우에 맞는가?
│     │  └─ NO → Context Engineering 필요 ⭐
│     │
│     ├─ 멀티턴 대화인가?
│     │  └─ YES → Context Engineering 필요 ⭐
│     │
│     └─ 비용이 중요한가?
│        └─ YES → Context Engineering 필요 ⭐
```

## 다음 단계

Context Engineering의 기본 개념을 이해했다면, 다음 문서들을 읽어보세요:

1. [컨텍스트 윈도우 관리](./context-window-management.md) - 윈도우 크기 계산 및 관리
2. [토큰 경제학](./token-economics.md) - 비용 최적화 전략

## 핵심 정리

| 구분 | Prompt Engineering | RAG | Context Engineering |
|------|-------------------|-----|---------------------|
| **입력** | 프롬프트 템플릿 | 쿼리 | 전체 컨텍스트 |
| **출력** | 최적화된 프롬프트 | 관련 문서 | 최적화된 컨텍스트 |
| **최적화 목표** | 명확성 | 관련성 | 효율성 + 품질 |
| **주요 기법** | Few-shot, CoT | Vector search | Compression, Prioritization |
| **적용 시점** | 항상 | 외부 지식 필요 시 | 복잡한 컨텍스트 관리 시 |

**Remember:** Context Engineering은 Prompt Engineering과 RAG를 대체하는 것이 아니라, 그 위에 구축되는 레이어입니다!

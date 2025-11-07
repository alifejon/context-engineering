# 하이브리드 검색 패턴

## 개요
여러 검색 방법을 결합하여 더 나은 컨텍스트를 구성합니다.

## 검색 방법 조합

### 1. 벡터 + 키워드
```python
def hybrid_search(query: str, k: int = 10):
    """벡터 검색 + BM25 키워드 검색"""
    # 벡터 검색
    vector_results = vector_store.similarity_search(query, k=k)

    # 키워드 검색
    keyword_results = bm25_search(query, k=k)

    # 결과 병합 및 리랭킹
    combined = merge_and_rerank(vector_results, keyword_results)
    return combined[:k]
```

### 2. 다중 쿼리 확장
```python
def multi_query_retrieval(query: str):
    """쿼리를 여러 버전으로 확장"""
    # LLM으로 쿼리 변형 생성
    query_variations = llm_generate_variations(query)

    # 각 변형으로 검색
    all_results = []
    for q in query_variations:
        results = vector_store.similarity_search(q, k=5)
        all_results.extend(results)

    # 중복 제거 및 리랭킹
    unique_results = deduplicate_and_rerank(all_results, query)
    return unique_results
```

### 3. 계층적 검색
```python
def hierarchical_retrieval(query: str):
    """큰 단위 → 작은 단위 검색"""
    # 1단계: 관련 섹션/챕터 찾기
    relevant_sections = search_sections(query)

    # 2단계: 해당 섹션 내에서 상세 검색
    detailed_results = []
    for section in relevant_sections[:3]:
        chunks = search_within_section(section, query)
        detailed_results.extend(chunks)

    return detailed_results
```

## 요약
다양한 검색 방법을 조합하면 더 포괄적이고 정확한 컨텍스트 구성 가능

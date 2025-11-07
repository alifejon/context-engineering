# 컨텍스트 우선순위화

## 개요

모든 컨텍스트가 동등하게 중요한 것은 아닙니다. 컨텍스트 우선순위화는 제한된 토큰 예산 내에서 가장 중요한 정보를 선택하고 배치하는 기법입니다.

## 우선순위화의 필요성

```python
# RAG 검색 결과
retrieved_docs = [
    {"content": "...", "score": 0.92},  # 매우 관련성 높음
    {"content": "...", "score": 0.89},  # 높음
    {"content": "...", "score": 0.75},  # 중간
    {"content": "...", "score": 0.68},  # 낮음
    {"content": "...", "score": 0.52},  # 매우 낮음
]

# 문제: 모두 포함하면 토큰 초과
# 해결: 우선순위 기반 선택
```

## 우선순위화 기준

### 1. 관련성 (Relevance)

```python
class RelevanceScorer:
    """관련성 기반 점수화"""

    def score_by_relevance(
        self,
        documents: list[dict],
        query: str
    ) -> list[dict]:
        """쿼리와의 관련성으로 점수 부여"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # 문서 + 쿼리 벡터화
        texts = [doc["content"] for doc in documents] + [query]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(texts)

        # 쿼리와의 유사도 계산
        query_vector = vectors[-1]
        doc_vectors = vectors[:-1]
        similarities = cosine_similarity(doc_vectors, query_vector).flatten()

        # 점수 추가
        for i, doc in enumerate(documents):
            doc["relevance_score"] = float(similarities[i])

        return sorted(documents, key=lambda x: x["relevance_score"], reverse=True)

# 사용
scorer = RelevanceScorer()
prioritized = scorer.score_by_relevance(documents, user_query)
```

### 2. 최신성 (Recency)

```python
from datetime import datetime, timedelta

class RecencyScorer:
    """최신성 기반 점수화"""

    def score_by_recency(
        self,
        documents: list[dict],  # {"content": str, "timestamp": datetime}
        decay_days: int = 30
    ) -> list[dict]:
        """시간에 따른 감쇠 점수"""
        now = datetime.now()

        for doc in documents:
            age_days = (now - doc["timestamp"]).days

            # 지수 감쇠
            decay_factor = 0.5 ** (age_days / decay_days)
            doc["recency_score"] = decay_factor

        return sorted(documents, key=lambda x: x["recency_score"], reverse=True)

# 사용 예시
docs = [
    {"content": "...", "timestamp": datetime.now() - timedelta(days=1)},   # 어제
    {"content": "...", "timestamp": datetime.now() - timedelta(days=30)},  # 한달전
    {"content": "...", "timestamp": datetime.now() - timedelta(days=90)},  # 3개월전
]

scorer = RecencyScorer()
prioritized = scorer.score_by_recency(docs, decay_days=30)
# 점수: 0.98, 0.50, 0.13
```

### 3. 신뢰도 (Credibility)

```python
class CredibilityScorer:
    """출처 신뢰도 기반 점수화"""

    def __init__(self):
        # 출처별 신뢰도 가중치
        self.source_weights = {
            "official_docs": 1.0,
            "verified_articles": 0.8,
            "community_posts": 0.5,
            "user_generated": 0.3
        }

    def score_by_credibility(self, documents: list[dict]) -> list[dict]:
        """출처 신뢰도로 점수 부여"""
        for doc in documents:
            source_type = doc.get("source_type", "unknown")
            doc["credibility_score"] = self.source_weights.get(source_type, 0.2)

        return documents

# 사용
scorer = CredibilityScorer()
scored = scorer.score_by_credibility(documents)
```

### 4. 구체성 (Specificity)

```python
class SpecificityScorer:
    """내용 구체성 평가"""

    def score_by_specificity(self, documents: list[dict]) -> list[dict]:
        """구체적인 정보를 우선"""
        for doc in documents:
            content = doc["content"]

            # 구체성 지표
            has_numbers = self.count_numbers(content)
            has_examples = self.count_examples(content)
            has_specific_terms = self.count_specific_terms(content)
            content_length = len(content.split())

            # 점수 계산
            specificity = (
                (has_numbers * 0.3) +
                (has_examples * 0.4) +
                (has_specific_terms * 0.3)
            ) / max(1, content_length / 100)  # 길이로 정규화

            doc["specificity_score"] = specificity

        return documents

    def count_numbers(self, text: str) -> int:
        import re
        return len(re.findall(r'\d+', text))

    def count_examples(self, text: str) -> int:
        example_keywords = ["예를 들어", "예시", "for example", "such as"]
        return sum(text.lower().count(kw) for kw in example_keywords)

    def count_specific_terms(self, text: str) -> int:
        # 구체적 용어 (전문 용어, 고유명사 등)
        # 간단한 휴리스틱: 대문자로 시작하는 단어
        import re
        return len(re.findall(r'\b[A-Z][a-z]+\b', text))
```

## 복합 점수화 (Composite Scoring)

```python
class CompositeScorer:
    """여러 기준을 결합한 점수화"""

    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "relevance": 0.4,
            "recency": 0.2,
            "credibility": 0.2,
            "specificity": 0.2
        }

        self.relevance_scorer = RelevanceScorer()
        self.recency_scorer = RecencyScorer()
        self.credibility_scorer = CredibilityScorer()
        self.specificity_scorer = SpecificityScorer()

    def score_documents(
        self,
        documents: list[dict],
        query: str
    ) -> list[dict]:
        """종합 점수 계산"""
        # 각 기준별 점수 계산
        docs = self.relevance_scorer.score_by_relevance(documents, query)
        docs = self.recency_scorer.score_by_recency(docs)
        docs = self.credibility_scorer.score_by_credibility(docs)
        docs = self.specificity_scorer.score_by_specificity(docs)

        # 종합 점수 계산
        for doc in docs:
            composite_score = (
                doc.get("relevance_score", 0) * self.weights["relevance"] +
                doc.get("recency_score", 0) * self.weights["recency"] +
                doc.get("credibility_score", 0) * self.weights["credibility"] +
                doc.get("specificity_score", 0) * self.weights["specificity"]
            )
            doc["composite_score"] = composite_score

        # 종합 점수로 정렬
        return sorted(docs, key=lambda x: x["composite_score"], reverse=True)

    def adapt_weights(self, query_type: str):
        """쿼리 유형에 따라 가중치 조정"""
        if query_type == "factual":
            # 사실 확인: 신뢰도와 구체성 중요
            self.weights = {
                "relevance": 0.3,
                "recency": 0.1,
                "credibility": 0.4,
                "specificity": 0.2
            }
        elif query_type == "recent_news":
            # 최신 뉴스: 최신성과 관련성 중요
            self.weights = {
                "relevance": 0.4,
                "recency": 0.4,
                "credibility": 0.1,
                "specificity": 0.1
            }
        elif query_type == "how_to":
            # 방법 안내: 구체성과 관련성 중요
            self.weights = {
                "relevance": 0.4,
                "recency": 0.1,
                "credibility": 0.2,
                "specificity": 0.3
            }

# 사용 예시
scorer = CompositeScorer()

# 쿼리 유형에 따라 가중치 조정
scorer.adapt_weights("how_to")

# 점수 계산
prioritized_docs = scorer.score_documents(documents, user_query)

# 상위 N개 선택
top_n = prioritized_docs[:5]
```

## 동적 우선순위화

```python
class DynamicPrioritizer:
    """상황에 따라 동적으로 우선순위 조정"""

    def __init__(self):
        self.user_feedback = []  # 사용자 피드백 기록
        self.performance_history = {}  # 성능 기록

    def prioritize(
        self,
        documents: list[dict],
        query: str,
        context: dict
    ) -> list[dict]:
        """컨텍스트 기반 동적 우선순위화"""

        # 사용자 프로필 기반 조정
        user_preferences = context.get("user_preferences", {})
        if user_preferences.get("prefer_recent"):
            recency_weight = 0.4
        else:
            recency_weight = 0.2

        # 대화 히스토리 기반 조정
        conversation_history = context.get("conversation_history", [])
        if len(conversation_history) > 5:
            # 긴 대화: 최근 대화 맥락 중요
            relevance_weight = 0.5
        else:
            relevance_weight = 0.4

        # 성능 피드백 기반 학습
        optimal_weights = self.learn_from_feedback()

        # 가중치 적용
        scorer = CompositeScorer(weights=optimal_weights)
        return scorer.score_documents(documents, query)

    def learn_from_feedback(self) -> dict:
        """피드백으로부터 최적 가중치 학습"""
        if not self.user_feedback:
            return {
                "relevance": 0.4,
                "recency": 0.2,
                "credibility": 0.2,
                "specificity": 0.2
            }

        # 간단한 학습 로직 (실제로는 더 정교한 ML 사용)
        # 긍정 피드백이 많은 가중치 조합을 찾음
        # ... 구현 생략

        return self.performance_history.get("best_weights", {})

    def record_feedback(
        self,
        query: str,
        documents: list[dict],
        user_rating: float,  # 0.0 ~ 1.0
        weights_used: dict
    ):
        """피드백 기록"""
        self.user_feedback.append({
            "query": query,
            "rating": user_rating,
            "weights": weights_used,
            "timestamp": datetime.now()
        })

        # 최고 성능 가중치 업데이트
        if user_rating > 0.8:
            self.performance_history["best_weights"] = weights_used
```

## 컨텍스트 배치 전략

우선순위화 후 어떻게 배치할 것인가?

```python
class ContextPlacer:
    """컨텍스트 배치 전략"""

    def place_contexts(
        self,
        contexts: list[dict],
        strategy: str = "priority_sandwich"
    ) -> str:
        """전략에 따라 컨텍스트 배치"""

        if strategy == "priority_first":
            # 높은 우선순위부터 순서대로
            return self._priority_first(contexts)

        elif strategy == "priority_sandwich":
            # 높은 우선순위를 시작과 끝에 (Lost in the Middle 대응)
            return self._priority_sandwich(contexts)

        elif strategy == "priority_clusters":
            # 유사한 주제끼리 그룹화
            return self._priority_clusters(contexts)

    def _priority_first(self, contexts: list[dict]) -> str:
        """우선순위 순서대로 배치"""
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.get("composite_score", 0),
            reverse=True
        )
        return "\n\n".join([ctx["content"] for ctx in sorted_contexts])

    def _priority_sandwich(self, contexts: list[dict]) -> str:
        """
        높은 우선순위를 시작과 끝에 배치
        Lost in the Middle 문제 해결
        """
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.get("composite_score", 0),
            reverse=True
        )

        if len(sorted_contexts) <= 2:
            return self._priority_first(contexts)

        # 상위 절반을 분할
        n = len(sorted_contexts)
        high_priority_count = n // 2

        first_half = sorted_contexts[:high_priority_count]
        second_half = sorted_contexts[high_priority_count:]

        # 재배치: 고우선순위를 앞뒤에
        reordered = []
        for i in range(len(first_half)):
            if i % 2 == 0:
                reordered.insert(0, first_half[i])  # 앞에
            else:
                reordered.append(first_half[i])     # 뒤에

        # 중간에 낮은 우선순위
        middle_idx = len(reordered) // 2
        for ctx in second_half:
            reordered.insert(middle_idx, ctx)

        return "\n\n".join([ctx["content"] for ctx in reordered])

    def _priority_clusters(self, contexts: list[dict]) -> str:
        """주제별 클러스터링 후 우선순위 순서로 배치"""
        # 간단한 구현: 키워드 기반 그룹화
        from collections import defaultdict

        clusters = defaultdict(list)

        for ctx in contexts:
            # 주제 식별 (간단한 휴리스틱)
            topic = self._identify_topic(ctx["content"])
            clusters[topic].append(ctx)

        # 각 클러스터 내에서 우선순위 정렬
        result = []
        for topic, topic_contexts in clusters.items():
            sorted_topic = sorted(
                topic_contexts,
                key=lambda x: x.get("composite_score", 0),
                reverse=True
            )
            result.append(f"## {topic}\n")
            result.extend([ctx["content"] for ctx in sorted_topic])
            result.append("\n")

        return "\n\n".join(result)

    def _identify_topic(self, text: str) -> str:
        """텍스트의 주제 식별"""
        # 간단한 키워드 기반 분류
        keywords_map = {
            "pricing": ["price", "cost", "fee", "payment"],
            "technical": ["api", "code", "implementation"],
            "support": ["help", "issue", "problem", "error"]
        }

        text_lower = text.lower()
        for topic, keywords in keywords_map.items():
            if any(kw in text_lower for kw in keywords):
                return topic

        return "general"

# 사용 예시
placer = ContextPlacer()
final_context = placer.place_contexts(
    prioritized_documents,
    strategy="priority_sandwich"
)
```

## 실전 파이프라인

```python
class PrioritizationPipeline:
    """전체 우선순위화 파이프라인"""

    def __init__(self):
        self.scorer = CompositeScorer()
        self.placer = ContextPlacer()

    def process(
        self,
        documents: list[dict],
        query: str,
        max_tokens: int,
        query_type: str = None
    ) -> dict:
        """우선순위화 파이프라인 실행"""

        # 1. 쿼리 유형에 따라 가중치 조정
        if query_type:
            self.scorer.adapt_weights(query_type)

        # 2. 문서 점수화
        scored_docs = self.scorer.score_documents(documents, query)

        # 3. 토큰 예산에 맞게 선택
        selected_docs = self._select_within_budget(scored_docs, max_tokens)

        # 4. 최적 배치
        final_context = self.placer.place_contexts(
            selected_docs,
            strategy="priority_sandwich"
        )

        return {
            "context": final_context,
            "selected_count": len(selected_docs),
            "total_count": len(documents),
            "tokens_used": count_tokens(final_context),
            "avg_score": sum(d["composite_score"] for d in selected_docs) / len(selected_docs)
        }

    def _select_within_budget(
        self,
        documents: list[dict],
        max_tokens: int
    ) -> list[dict]:
        """토큰 예산 내에서 최대한 선택"""
        selected = []
        total_tokens = 0

        for doc in documents:
            doc_tokens = count_tokens(doc["content"])
            if total_tokens + doc_tokens <= max_tokens:
                selected.append(doc)
                total_tokens += doc_tokens
            else:
                break

        return selected

# 사용
pipeline = PrioritizationPipeline()
result = pipeline.process(
    documents=rag_results,
    query=user_query,
    max_tokens=4000,
    query_type="how_to"
)

print(f"Selected {result['selected_count']} / {result['total_count']} documents")
print(f"Tokens used: {result['tokens_used']} / 4000")
print(f"Average score: {result['avg_score']:.2f}")
```

## 요약

**우선순위화 기준:**
1. 관련성 - 쿼리와의 유사도
2. 최신성 - 시간 기반 감쇠
3. 신뢰도 - 출처 신뢰성
4. 구체성 - 정보의 구체성

**배치 전략:**
- Priority First: 단순 우선순위 순
- Priority Sandwich: 고우선순위를 앞뒤에
- Priority Clusters: 주제별 그룹화

**핵심**: 제한된 토큰으로 최대 가치 추출!

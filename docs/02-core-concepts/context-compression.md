# 컨텍스트 압축 (Context Compression)

## 개요

컨텍스트 압축은 정보의 본질을 유지하면서 토큰 수를 줄이는 기법입니다. RAG에서 검색한 많은 문서를 제한된 컨텍스트 윈도우에 효율적으로 담기 위해 필수적입니다.

## 왜 압축이 필요한가?

### RAG의 딜레마

```python
# RAG 시스템의 전형적인 문제
query = "컨텍스트 엔지니어링이란?"

# 벡터 검색으로 상위 10개 문서 검색
docs = vector_store.similarity_search(query, k=10)
total_tokens = sum(count_tokens(doc.content) for doc in docs)
# → 15,000 tokens

# 문제:
# 1. 컨텍스트 윈도우 초과 (예: GPT-4 8K)
# 2. 높은 비용 (15K tokens × $0.03 / 1K = $0.45 per query)
# 3. 관련 없는 정보 포함
# 4. Lost in the middle 효과
```

### 압축의 목표

1. **토큰 절감**: 30-80% 토큰 감소
2. **정보 보존**: 핵심 정보 95%+ 유지
3. **관련성 향상**: 불필요한 정보 제거
4. **비용 절감**: 월간 수천~수만 달러 절감

## 압축 기법

### 1. 추출형 압축 (Extractive Compression)

원문에서 중요한 문장/구절을 선택하여 추출.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ExtractiveSummarizer:
    """추출형 요약기"""

    def __init__(self, compression_ratio: float = 0.3):
        self.compression_ratio = compression_ratio

    def compress(self, text: str, query: str = None) -> str:
        """텍스트를 압축"""
        sentences = self.split_sentences(text)

        if not sentences:
            return text

        # 문장 중요도 계산
        if query:
            scores = self.score_sentences_with_query(sentences, query)
        else:
            scores = self.score_sentences(sentences)

        # 상위 N% 문장 선택
        n_select = max(1, int(len(sentences) * self.compression_ratio))
        top_indices = np.argsort(scores)[-n_select:]
        top_indices = sorted(top_indices)  # 원래 순서 유지

        return " ".join([sentences[i] for i in top_indices])

    def split_sentences(self, text: str) -> list[str]:
        """문장 분리"""
        import re
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def score_sentences(self, sentences: list[str]) -> np.ndarray:
        """TF-IDF 기반 문장 점수"""
        if len(sentences) == 1:
            return np.array([1.0])

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)

        # 평균 TF-IDF 점수
        scores = np.asarray(tfidf_matrix.mean(axis=1)).flatten()
        return scores

    def score_sentences_with_query(
        self,
        sentences: list[str],
        query: str
    ) -> np.ndarray:
        """쿼리 관련성 기반 문장 점수"""
        if len(sentences) == 1:
            return np.array([1.0])

        vectorizer = TfidfVectorizer()
        all_texts = sentences + [query]
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # 각 문장과 쿼리의 유사도
        query_vector = tfidf_matrix[-1]
        sentence_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(sentence_vectors, query_vector).flatten()

        return similarities

# 사용 예시
text = """
Context engineering is a systematic approach to managing LLM context windows.
It involves techniques like compression, prioritization, and dynamic assembly.
The weather today is sunny and warm.
Context windows are limited in size, typically 4K to 128K tokens.
Effective context management can reduce costs by 50-80%.
My favorite color is blue.
"""

query = "What is context engineering?"

summarizer = ExtractiveSummarizer(compression_ratio=0.5)
compressed = summarizer.compress(text, query)

print(f"Original: {count_tokens(text)} tokens")
print(f"Compressed: {count_tokens(compressed)} tokens")
print(f"Compression: {(1 - count_tokens(compressed)/count_tokens(text))*100:.1f}%")
print(f"\nResult:\n{compressed}")

# Output:
# Original: 89 tokens
# Compressed: 45 tokens
# Compression: 49.4%
#
# Result:
# Context engineering is a systematic approach to managing LLM context windows.
# It involves techniques like compression, prioritization, and dynamic assembly.
# Context windows are limited in size, typically 4K to 128K tokens.
```

**장점:**
- 원문의 정확한 표현 유지
- 빠른 처리 속도
- 사실 왜곡 위험 낮음

**단점:**
- 압축률 제한적 (보통 30-50%)
- 문장 간 중복 제거 어려움

### 2. 생성형 압축 (Abstractive Compression)

LLM을 사용하여 내용을 재작성하고 요약.

```python
class AbstractiveSummarizer:
    """생성형 요약기"""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    def compress(
        self,
        text: str,
        target_tokens: int = None,
        query: str = None
    ) -> str:
        """텍스트를 생성형 요약으로 압축"""
        current_tokens = count_tokens(text)

        if target_tokens is None:
            target_tokens = current_tokens // 2

        # 요약 프롬프트 생성
        prompt = self.build_prompt(text, target_tokens, query)

        # LLM으로 요약
        response = self.call_llm(prompt)

        return response

    def build_prompt(
        self,
        text: str,
        target_tokens: int,
        query: str = None
    ) -> str:
        """요약 프롬프트 생성"""
        base_prompt = f"""다음 텍스트를 약 {target_tokens} 토큰으로 요약하세요.
핵심 정보만 포함하고 불필요한 내용은 제거하세요.

텍스트:
{text}

요약:"""

        if query:
            base_prompt = f"""다음 텍스트를 약 {target_tokens} 토큰으로 요약하세요.
특히 다음 질문과 관련된 정보에 집중하세요: "{query}"

텍스트:
{text}

요약:"""

        return base_prompt

    def call_llm(self, prompt: str) -> str:
        """LLM 호출 (구현 필요)"""
        # OpenAI API 호출 등
        pass

# 사용 예시
text = """
Context engineering is a sophisticated methodology for optimizing
the management of context windows in Large Language Model applications.
It encompasses various advanced techniques including intelligent
compression algorithms, strategic prioritization frameworks, and
dynamic context assembly mechanisms. These approaches are designed
to maximize the efficient utilization of limited context window
resources while maintaining high quality outputs. The field has
emerged as a critical discipline in production LLM systems, where
cost optimization and performance are paramount concerns.
"""

summarizer = AbstractiveSummarizer()
compressed = summarizer.compress(text, target_tokens=30)

# Expected output (약 30 tokens):
# "Context engineering optimizes LLM context windows through
#  compression, prioritization, and dynamic assembly to reduce
#  costs while maintaining quality."
```

**장점:**
- 높은 압축률 (50-80%)
- 중복 제거 및 재구성
- 자연스러운 표현

**단점:**
- 추가 LLM 호출 비용
- 사실 왜곡 가능성
- 처리 시간 증가

### 3. 하이브리드 압축

추출형과 생성형을 결합.

```python
class HybridCompressor:
    """하이브리드 압축기"""

    def __init__(self):
        self.extractive = ExtractiveSummarizer(compression_ratio=0.5)
        self.abstractive = AbstractiveSummarizer()

    def compress(
        self,
        text: str,
        target_tokens: int,
        query: str = None
    ) -> str:
        """2단계 압축"""
        current_tokens = count_tokens(text)

        if current_tokens <= target_tokens:
            return text

        # Stage 1: 추출형으로 50% 압축
        extracted = self.extractive.compress(text, query)
        extracted_tokens = count_tokens(extracted)

        # Stage 2: 아직 목표 초과 시 생성형 압축
        if extracted_tokens > target_tokens:
            compressed = self.abstractive.compress(
                extracted,
                target_tokens=target_tokens,
                query=query
            )
            return compressed

        return extracted

# 비용 및 품질 비교
# Original: 1000 tokens
# Extractive only: 500 tokens (품질: 95%, 비용: $0)
# Abstractive only: 300 tokens (품질: 90%, 비용: $0.001)
# Hybrid: 300 tokens (품질: 93%, 비용: $0.0005)
```

### 4. 의미적 압축 (Semantic Compression)

의미가 유사한 내용을 병합하고 중복 제거.

```python
class SemanticCompressor:
    """의미적 압축기"""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold

    def compress(self, documents: list[str]) -> list[str]:
        """의미적으로 유사한 문서 병합"""
        if not documents:
            return []

        # 문서 임베딩
        embeddings = self.embed_documents(documents)

        # 유사도 매트릭스 계산
        similarity_matrix = cosine_similarity(embeddings)

        # 클러스터링
        clusters = self.cluster_similar(similarity_matrix)

        # 각 클러스터에서 대표 문서 선택 또는 병합
        compressed_docs = []
        for cluster in clusters:
            if len(cluster) == 1:
                compressed_docs.append(documents[cluster[0]])
            else:
                # 클러스터 내 문서들을 병합
                merged = self.merge_documents([documents[i] for i in cluster])
                compressed_docs.append(merged)

        return compressed_docs

    def embed_documents(self, documents: list[str]) -> np.ndarray:
        """문서 임베딩 (간단한 TF-IDF 사용)"""
        vectorizer = TfidfVectorizer()
        return vectorizer.fit_transform(documents).toarray()

    def cluster_similar(self, similarity_matrix: np.ndarray) -> list[list[int]]:
        """유사도 기반 클러스터링"""
        n = len(similarity_matrix)
        visited = set()
        clusters = []

        for i in range(n):
            if i in visited:
                continue

            cluster = [i]
            visited.add(i)

            for j in range(i + 1, n):
                if j not in visited and similarity_matrix[i][j] > self.threshold:
                    cluster.append(j)
                    visited.add(j)

            clusters.append(cluster)

        return clusters

    def merge_documents(self, documents: list[str]) -> str:
        """문서 병합 (중복 제거)"""
        # 간단한 구현: 모든 고유 문장 추출
        all_sentences = []
        seen = set()

        for doc in documents:
            sentences = doc.split('. ')
            for sent in sentences:
                sent = sent.strip()
                if sent and sent not in seen:
                    all_sentences.append(sent)
                    seen.add(sent)

        return '. '.join(all_sentences)

# 사용 예시
docs = [
    "Context engineering manages LLM context windows efficiently.",
    "Context engineering is about efficient management of LLM context.",
    "RAG retrieves relevant documents from a knowledge base.",
    "Context windows have limited capacity in tokens.",
    "Token limits vary by model, from 4K to 1M tokens."
]

compressor = SemanticCompressor(similarity_threshold=0.85)
compressed = compressor.compress(docs)

print(f"Original: {len(docs)} documents")
print(f"Compressed: {len(compressed)} documents")
# → 유사한 첫 두 문서가 하나로 병합됨
```

## 압축 전략 선택 가이드

```python
def choose_compression_strategy(
    text_length: int,
    target_compression: float,
    quality_priority: str,  # "speed", "quality", "cost"
    budget: float
) -> str:
    """상황에 맞는 압축 전략 선택"""

    if quality_priority == "speed":
        # 빠른 처리가 중요
        if target_compression < 0.5:
            return "extractive"
        else:
            return "semantic"

    elif quality_priority == "cost":
        # 비용 최소화
        if text_length < 5000:
            return "extractive"  # LLM 호출 없음
        else:
            return "hybrid"  # 추출로 먼저 줄이고 필요시 생성

    else:  # quality
        # 최고 품질
        if target_compression < 0.4:
            return "extractive"
        elif target_compression < 0.7:
            return "hybrid"
        else:
            return "abstractive"

# 의사결정 매트릭스
"""
압축률 | 속도 우선 | 비용 우선 | 품질 우선
-------|----------|----------|----------
< 40%  | 추출형    | 추출형    | 추출형
40-60% | 추출형    | 하이브리드 | 하이브리드
60-80% | 의미적    | 하이브리드 | 생성형
> 80%  | 의미적    | 생성형    | 생성형
"""
```

## 압축 품질 평가

```python
class CompressionEvaluator:
    """압축 품질 평가"""

    def evaluate(
        self,
        original: str,
        compressed: str,
        query: str = None
    ) -> dict:
        """압축 결과 평가"""

        # 1. 압축률
        compression_ratio = 1 - (count_tokens(compressed) / count_tokens(original))

        # 2. 정보 보존율 (간단한 키워드 기반)
        info_retention = self.calculate_info_retention(original, compressed)

        # 3. 쿼리 관련성 (query가 있는 경우)
        if query:
            relevance = self.calculate_relevance(compressed, query)
        else:
            relevance = None

        # 4. 가독성
        readability = self.calculate_readability(compressed)

        return {
            "compression_ratio": f"{compression_ratio * 100:.1f}%",
            "info_retention": f"{info_retention * 100:.1f}%",
            "query_relevance": f"{relevance * 100:.1f}%" if relevance else "N/A",
            "readability_score": f"{readability:.2f}",
            "overall_score": self.calculate_overall_score(
                compression_ratio, info_retention, relevance, readability
            )
        }

    def calculate_info_retention(self, original: str, compressed: str) -> float:
        """정보 보존율 계산"""
        # 간단한 방법: 중요 키워드 보존율
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer(max_features=20)
        vectorizer.fit([original])

        # 원문의 상위 키워드
        feature_names = vectorizer.get_feature_names_out()
        original_keywords = set(feature_names)

        # 압축본에 포함된 키워드
        compressed_lower = compressed.lower()
        retained_keywords = sum(
            1 for kw in original_keywords if kw in compressed_lower
        )

        return retained_keywords / len(original_keywords) if original_keywords else 0

    def calculate_relevance(self, text: str, query: str) -> float:
        """쿼리 관련성 계산"""
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text, query])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity

    def calculate_readability(self, text: str) -> float:
        """가독성 점수 (간단한 휴리스틱)"""
        sentences = text.split('.')
        if not sentences:
            return 0

        words = text.split()
        avg_sentence_length = len(words) / len(sentences)

        # 이상적인 문장 길이: 15-20 단어
        if 15 <= avg_sentence_length <= 20:
            return 1.0
        elif avg_sentence_length < 15:
            return 0.8 + (avg_sentence_length / 15) * 0.2
        else:
            return max(0, 1.0 - (avg_sentence_length - 20) / 20)

    def calculate_overall_score(
        self,
        compression: float,
        retention: float,
        relevance: float,
        readability: float
    ) -> str:
        """종합 점수"""
        # 가중 평균
        weights = {
            "compression": 0.2,
            "retention": 0.4,
            "relevance": 0.3 if relevance else 0,
            "readability": 0.1
        }

        if relevance is None:
            # relevance 없으면 가중치 재분배
            weights["retention"] += weights["relevance"]
            weights["relevance"] = 0

        score = (
            compression * weights["compression"] +
            retention * weights["retention"] +
            (relevance or 0) * weights["relevance"] +
            readability * weights["readability"]
        )

        if score >= 0.8:
            return f"{score:.2f} (Excellent)"
        elif score >= 0.6:
            return f"{score:.2f} (Good)"
        elif score >= 0.4:
            return f"{score:.2f} (Fair)"
        else:
            return f"{score:.2f} (Poor)"

# 사용 예시
evaluator = CompressionEvaluator()
result = evaluator.evaluate(original_text, compressed_text, query)
print(result)
```

## 실전 압축 파이프라인

```python
class CompressionPipeline:
    """프로덕션 압축 파이프라인"""

    def __init__(self):
        self.extractive = ExtractiveSummarizer()
        self.semantic = SemanticCompressor()
        self.abstractive = AbstractiveSummarizer()
        self.evaluator = CompressionEvaluator()

    def compress_documents(
        self,
        documents: list[str],
        query: str,
        target_tokens: int,
        min_quality_score: float = 0.7
    ) -> dict:
        """문서 압축 파이프라인"""

        # Stage 1: 의미적 중복 제거
        deduped = self.semantic.compress(documents)
        combined = "\n\n".join(deduped)

        # Stage 2: 쿼리 기반 추출
        extracted = self.extractive.compress(combined, query)

        # Stage 3: 필요시 생성형 압축
        current_tokens = count_tokens(extracted)
        if current_tokens > target_tokens:
            final = self.abstractive.compress(
                extracted,
                target_tokens=target_tokens,
                query=query
            )
        else:
            final = extracted

        # 품질 평가
        evaluation = self.evaluator.evaluate(combined, final, query)

        return {
            "compressed_text": final,
            "original_tokens": count_tokens(combined),
            "compressed_tokens": count_tokens(final),
            "evaluation": evaluation,
            "stages": {
                "semantic_dedup": f"{len(documents)} → {len(deduped)} docs",
                "extractive": f"{count_tokens(combined)} → {count_tokens(extracted)} tokens",
                "abstractive": f"{count_tokens(extracted)} → {count_tokens(final)} tokens"
            }
        }
```

## 다음 단계

- [컨텍스트 우선순위화](./context-prioritization.md)
- [압축 예제 코드](../../examples/02-compression/)

## 요약

| 압축 방식 | 압축률 | 속도 | 비용 | 품질 | 사용 사례 |
|----------|-------|------|------|------|----------|
| 추출형 | 30-50% | 빠름 | 무료 | 높음 | 사실 정확성 중요 |
| 생성형 | 50-80% | 느림 | 높음 | 중간 | 높은 압축률 필요 |
| 의미적 | 20-40% | 중간 | 무료 | 높음 | 중복 문서 많음 |
| 하이브리드 | 40-70% | 중간 | 중간 | 높음 | 균형잡힌 접근 |

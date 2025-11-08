#!/usr/bin/env python3
"""
Embedding-Based Relevance Scoring

임베딩을 사용한 의미적 관련성 평가.
TF-IDF보다 더 정확한 semantic matching을 제공합니다.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    print_section,
    print_success,
    print_warning
)

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SimpleEmbeddingScorer:
    """
    간단한 임베딩 기반 점수화
    (실제 프로덕션에서는 OpenAI embeddings나 sentence-transformers 사용)
    """

    def __init__(self):
        self.vectorizer = None

    def score_documents(self, documents: list[str], query: str) -> list[dict]:
        """
        문서들에 의미적 관련성 점수 부여

        Args:
            documents: 문서 리스트
            query: 검색 쿼리

        Returns:
            점수가 포함된 문서 리스트
        """
        # 간단한 구현: TF-IDF를 임베딩처럼 사용
        # 실제로는 sentence-transformers나 OpenAI embeddings 사용
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),  # bigrams for better semantic capture
            stop_words='english'
        )

        # 벡터화
        all_texts = documents + [query]
        embeddings = self.vectorizer.fit_transform(all_texts).toarray()

        # 쿼리 임베딩
        query_embedding = embeddings[-1].reshape(1, -1)
        doc_embeddings = embeddings[:-1]

        # 코사인 유사도 계산
        similarities = cosine_similarity(doc_embeddings, query_embedding).flatten()

        # 결과 생성
        scored_docs = []
        for i, (doc, score) in enumerate(zip(documents, similarities)):
            scored_docs.append({
                'index': i,
                'content': doc,
                'score': float(score),
                'tokens': count_tokens(doc)
            })

        # 점수 순으로 정렬
        scored_docs.sort(key=lambda x: x['score'], reverse=True)

        return scored_docs


class ProductionEmbeddingScorer:
    """
    프로덕션용 임베딩 점수화
    OpenAI embeddings API 사용 예시
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.embedding_model = embedding_model
        self.cache = {}  # 임베딩 캐싱

    def get_embedding(self, text: str) -> np.ndarray:
        """텍스트의 임베딩 가져오기 (캐싱 포함)"""
        if text in self.cache:
            return self.cache[text]

        # 실제 사용시: OpenAI API 호출
        # from openai import OpenAI
        # client = OpenAI()
        # response = client.embeddings.create(
        #     model=self.embedding_model,
        #     input=text
        # )
        # embedding = np.array(response.data[0].embedding)

        # 데모용: TF-IDF로 대체
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=100)
        embedding = vectorizer.fit_transform([text]).toarray()[0]

        self.cache[text] = embedding
        return embedding

    def score_documents(self, documents: list[str], query: str) -> list[dict]:
        """문서들에 임베딩 기반 점수 부여"""
        query_embedding = self.get_embedding(query)

        scored_docs = []
        for i, doc in enumerate(documents):
            doc_embedding = self.get_embedding(doc)

            # 코사인 유사도
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )

            scored_docs.append({
                'index': i,
                'content': doc,
                'score': float(similarity),
                'tokens': count_tokens(doc)
            })

        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs


def demonstrate_embedding_scoring():
    """임베딩 기반 점수화 시연"""
    print_section("EMBEDDING-BASED SCORING DEMO")

    documents = [
        "Context engineering optimizes LLM token usage through compression and prioritization techniques.",
        "Machine learning models are trained on large datasets using gradient descent optimization.",
        "Token costs can be reduced by 60-80% with proper context management strategies.",
        "Deep neural networks consist of multiple layers that learn hierarchical representations.",
        "RAG systems combine retrieval with generation to provide contextually relevant responses.",
        "Python is widely used in data science for its extensive library ecosystem.",
        "Dynamic context assembly adapts prompts based on query type and complexity.",
        "Cloud computing infrastructure enables scalable deployment of ML models.",
        "Context compression maintains information quality while reducing token count.",
        "Database indexing improves query performance in large-scale applications.",
    ]

    query = "How to reduce LLM costs through context optimization?"

    print(f"Query: {query}\n")
    print(f"Documents to score: {len(documents)}\n")

    # 간단한 임베딩 점수화
    print("⏳ Calculating embedding-based relevance scores...\n")

    scorer = SimpleEmbeddingScorer()
    scored_docs = scorer.score_documents(documents, query)

    print_success("Scoring complete!\n")

    # 결과 표시
    print_section("EMBEDDING SCORES")

    print(f"{'Rank':<6} {'Score':<10} {'Tokens':<10} {'Preview':<50}")
    print("-" * 80)

    for i, doc in enumerate(scored_docs, 1):
        preview = doc['content'][:47] + "..." if len(doc['content']) > 50 else doc['content']
        score_bar = "█" * int(doc['score'] * 20)

        # 색상: 높은 점수 = 초록, 중간 = 노랑, 낮은 = 빨강
        if doc['score'] > 0.5:
            color = '\033[92m'  # Green
        elif doc['score'] > 0.3:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'

        print(f"{i:<6} {color}{doc['score']:<10.3f}{reset} {doc['tokens']:<10} {preview}")
        print(f"       {color}{score_bar}{reset}")

    # TF-IDF와 비교
    print_section("COMPARISON: TF-IDF vs EMBEDDINGS")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim

    # TF-IDF 점수
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    all_texts = documents + [query]
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
    tfidf_scores = cos_sim(tfidf_matrix[:-1], tfidf_matrix[-1:]).flatten()

    # 상위 5개 비교
    print("Top 5 documents comparison:\n")

    print(f"{'Rank':<6} {'TF-IDF Score':<15} {'Embedding Score':<18} {'Difference':<12}")
    print("-" * 55)

    for i in range(min(5, len(scored_docs))):
        doc_idx = scored_docs[i]['index']
        emb_score = scored_docs[i]['score']
        tfidf_score = tfidf_scores[doc_idx]
        diff = emb_score - tfidf_score

        print(f"{i+1:<6} {tfidf_score:<15.3f} {emb_score:<18.3f} {diff:+.3f}")

    print("\n💡 Observations:")
    print("  • Embeddings capture semantic meaning better")
    print("  • TF-IDF focuses on exact keyword matching")
    print("  • For this example, both methods work similarly")
    print("  • Real embeddings (OpenAI/sentence-transformers) show bigger differences")


def demonstrate_production_usage():
    """프로덕션 사용 예시"""
    print_section("PRODUCTION USAGE")

    print("Real-world embedding options:\n")

    print("1. OpenAI Embeddings:")
    print("   • Model: text-embedding-3-small")
    print("   • Cost: $0.02 per 1M tokens")
    print("   • Dimensions: 1536")
    print("   • Best for: General-purpose, high quality\n")

    print("2. OpenAI Embeddings (Large):")
    print("   • Model: text-embedding-3-large")
    print("   • Cost: $0.13 per 1M tokens")
    print("   • Dimensions: 3072")
    print("   • Best for: Highest accuracy needs\n")

    print("3. Sentence Transformers (Open Source):")
    print("   • Model: all-MiniLM-L6-v2")
    print("   • Cost: Free (self-hosted)")
    print("   • Dimensions: 384")
    print("   • Best for: Cost-sensitive, offline use\n")

    print("Example with OpenAI API:")
    print("```python")
    print("from openai import OpenAI")
    print("")
    print("client = OpenAI()")
    print("")
    print("def get_embedding(text, model='text-embedding-3-small'):")
    print("    response = client.embeddings.create(")
    print("        model=model,")
    print("        input=text")
    print("    )")
    print("    return response.data[0].embedding")
    print("")
    print("# Score documents")
    print("query_emb = get_embedding(query)")
    print("for doc in documents:")
    print("    doc_emb = get_embedding(doc)")
    print("    score = cosine_similarity(query_emb, doc_emb)")
    print("```\n")

    # 비용 분석
    print_section("COST ANALYSIS")

    docs_per_query = 100
    avg_tokens_per_doc = 200
    queries_per_month = 10_000

    total_docs_per_month = docs_per_query * queries_per_month
    total_tokens_per_month = total_docs_per_month * avg_tokens_per_doc

    cost_per_1m_tokens = 0.02  # text-embedding-3-small
    monthly_embedding_cost = (total_tokens_per_month / 1_000_000) * cost_per_1m_tokens

    print(f"Scenario:")
    print(f"  • {docs_per_query} documents scored per query")
    print(f"  • {avg_tokens_per_doc} avg tokens per document")
    print(f"  • {queries_per_month:,} queries per month\n")

    print(f"Total documents/month: {total_docs_per_month:,}")
    print(f"Total tokens/month: {total_tokens_per_month:,}")
    print(f"Monthly embedding cost: ${monthly_embedding_cost:.2f}\n")

    print("💡 Cost Optimization:")
    print("  1. Cache embeddings for repeated documents")
    print("  2. Pre-compute document embeddings offline")
    print("  3. Only embed query at runtime")
    print("  4. Use smaller embedding models when possible")

    # 캐싱 효과
    print_section("CACHING EFFECTIVENESS")

    cache_hit_rates = [0, 0.5, 0.8, 0.95]

    print(f"{'Cache Hit Rate':<20} {'Embeddings Needed':<20} {'Monthly Cost':<15}")
    print("-" * 55)

    for hit_rate in cache_hit_rates:
        embeddings_needed = total_docs_per_month * (1 - hit_rate)
        tokens_needed = embeddings_needed * avg_tokens_per_doc
        cost = (tokens_needed / 1_000_000) * cost_per_1m_tokens

        print(f"{hit_rate*100:.0f}%{'':<17} {embeddings_needed:,.0f}{'':<8} ${cost:.2f}")

    print("\n✓ With 80% cache hit rate: ${:.2f} → ${:.2f} (80% savings!)".format(
        monthly_embedding_cost,
        monthly_embedding_cost * 0.2
    ))


def main():
    demonstrate_embedding_scoring()
    print("\n" + "="*70 + "\n")
    demonstrate_production_usage()

    print("\n" + "="*70)
    print_section("BEST PRACTICES")

    print("1. When to use embeddings vs TF-IDF:")
    print("   ✓ Embeddings: Semantic similarity, paraphrases, cross-lingual")
    print("   ✓ TF-IDF: Exact keyword matching, speed-critical, simple queries")

    print("\n2. Embedding Selection:")
    print("   • Start with text-embedding-3-small (good balance)")
    print("   • Upgrade to large only if accuracy critical")
    print("   • Consider sentence-transformers for offline/cost-sensitive")

    print("\n3. Performance Optimization:")
    print("   • Pre-compute document embeddings")
    print("   • Implement aggressive caching")
    print("   • Batch embedding requests")
    print("   • Use async for parallel processing")

    print("\n4. Quality Monitoring:")
    print("   • Track average relevance scores")
    print("   • Monitor cache hit rates")
    print("   • A/B test different models")
    print("   • Validate with human judgments")

    print("\n💡 Next steps:")
    print("  • Implement with real embedding API")
    print("  • Add caching layer")
    print("  • Combine with recency/importance weights")
    print("  • Try hybrid TF-IDF + embeddings approach")


if __name__ == "__main__":
    main()

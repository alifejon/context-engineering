#!/usr/bin/env python3
"""
TF-IDF Based Relevance Scoring

TF-IDF를 사용하여 쿼리와의 관련성으로
문서의 우선순위를 매깁니다.
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
    get_sample_text
)


class TFIDFScorer:
    """TF-IDF 기반 관련성 점수화"""

    def __init__(self):
        self.vectorizer = None

    def score_documents(self, documents: list[str], query: str) -> list[dict]:
        """
        문서들에 관련성 점수 부여

        Args:
            documents: 문서 리스트
            query: 검색 쿼리

        Returns:
            점수가 포함된 문서 리스트
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # TF-IDF 벡터화
        self.vectorizer = TfidfVectorizer(stop_words='english')

        # 문서 + 쿼리 함께 벡터화
        all_texts = documents + [query]
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)

        # 쿼리와의 유사도 계산
        query_vector = tfidf_matrix[-1]
        doc_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(doc_vectors, query_vector).flatten()

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

    def select_top_k(
        self,
        scored_docs: list[dict],
        k: int = None,
        max_tokens: int = None
    ) -> list[dict]:
        """
        상위 K개 또는 토큰 예산 내에서 선택

        Args:
            scored_docs: 점수화된 문서들
            k: 선택할 문서 개수
            max_tokens: 최대 토큰 수

        Returns:
            선택된 문서들
        """
        if k is None and max_tokens is None:
            k = len(scored_docs)

        selected = []
        total_tokens = 0

        for doc in scored_docs:
            # K개 제한
            if k is not None and len(selected) >= k:
                break

            # 토큰 예산 제한
            if max_tokens is not None:
                if total_tokens + doc['tokens'] > max_tokens:
                    break

            selected.append(doc)
            total_tokens += doc['tokens']

        return selected


def demonstrate_relevance_scoring():
    """관련성 점수화 시연"""
    print_section("TF-IDF RELEVANCE SCORING DEMO")

    # 문서 세트 생성
    documents = [
        "Context engineering is a systematic approach to managing LLM context windows efficiently through compression and prioritization.",
        "Machine learning models require large amounts of training data to achieve good performance.",
        "Token economics focuses on understanding and optimizing the cost of LLM API calls.",
        "Context compression reduces the number of tokens while preserving essential information.",
        "Python is a popular programming language for data science and machine learning applications.",
        "RAG systems retrieve relevant documents from a knowledge base to augment LLM prompts.",
        "Context prioritization ranks information by relevance, recency, and importance.",
        "Deep learning has revolutionized computer vision and natural language processing.",
        "Dynamic context assembly builds prompts based on query type and complexity.",
        "Cloud computing provides scalable infrastructure for machine learning workloads.",
    ]

    query = "How does context engineering optimize LLM costs?"

    print(f"Query: {query}\n")
    print(f"Documents to score: {len(documents)}\n")

    # 점수 계산
    print("⏳ Calculating relevance scores...")

    scorer = TFIDFScorer()
    scored_docs = scorer.score_documents(documents, query)

    print_success("Scoring complete!\n")

    # 결과 표시
    print_section("RELEVANCE SCORES")

    print(f"{'Rank':<6} {'Score':<10} {'Tokens':<10} {'Preview':<50}")
    print(f"{'-'*80}")

    for i, doc in enumerate(scored_docs, 1):
        preview = doc['content'][:47] + "..." if len(doc['content']) > 50 else doc['content']
        score_bar = "█" * int(doc['score'] * 20)
        print(f"{i:<6} {doc['score']:<10.3f} {doc['tokens']:<10} {preview}")
        print(f"       {score_bar}")

    # 상위 문서 분석
    print_section("TOP 3 DOCUMENTS ANALYSIS")

    for i, doc in enumerate(scored_docs[:3], 1):
        print(f"\n{i}. Score: {doc['score']:.3f}")
        print(f"   Content: {doc['content']}")
        print(f"   Tokens: {doc['tokens']}")

        # 쿼리와의 공통 키워드 (간단한 분석)
        query_words = set(query.lower().split())
        doc_words = set(doc['content'].lower().split())
        common = query_words & doc_words
        if common:
            print(f"   Common keywords: {', '.join(common)}")

    # 토큰 예산 기반 선택
    print_section("TOKEN BUDGET SELECTION")

    max_tokens = 500
    selected = scorer.select_top_k(scored_docs, max_tokens=max_tokens)

    print(f"Budget: {format_tokens(max_tokens)}")
    print(f"Selected: {len(selected)} documents")
    print(f"Total tokens: {format_tokens(sum(d['tokens'] for d in selected))}")
    print(f"Average score: {sum(d['score'] for d in selected) / len(selected):.3f}\n")

    print("Selected documents:")
    for i, doc in enumerate(selected, 1):
        print(f"  {i}. [Score: {doc['score']:.3f}] {doc['content'][:60]}...")

    # Top-K 비교
    print_section("TOP-K COMPARISON")

    k_values = [3, 5, 10]

    print(f"{'K Value':<10} {'Docs':<10} {'Total Tokens':<15} {'Avg Score':<15}")
    print(f"{'-'*55}")

    for k in k_values:
        selected_k = scorer.select_top_k(scored_docs, k=k)
        total_tokens = sum(d['tokens'] for d in selected_k)
        avg_score = sum(d['score'] for d in selected_k) / len(selected_k)

        print(f"{k:<10} {len(selected_k):<10} {total_tokens:<15} {avg_score:<15.3f}")

    # 실전 권장사항
    print_section("BEST PRACTICES")

    print("1. 검색 단계:")
    print("   • 초기에 많은 문서 검색 (예: 20-50개)")
    print("   • 벡터 검색만으로는 불완전할 수 있음")

    print("\n2. 점수화 단계:")
    print("   • TF-IDF로 쿼리 관련성 재평가")
    print("   • 리랭킹으로 품질 향상")

    print("\n3. 선택 단계:")
    print("   • 토큰 예산 내에서 상위 문서 선택")
    print("   • 일반적으로 상위 5-10개면 충분")

    print("\n4. 검증:")
    print("   • 평균 점수가 0.3 이상이면 양호")
    print("   • 0.3 미만이면 검색 쿼리 개선 필요")

    avg_score_top5 = sum(d['score'] for d in scored_docs[:5]) / 5
    print(f"\n현재 상위 5개 평균 점수: {avg_score_top5:.3f}")

    if avg_score_top5 >= 0.3:
        print_success("✓ Good relevance!")
    else:
        print(f"⚠ Low relevance. Consider improving query.")

    print_success("\nRelevance scoring complete!")


def main():
    demonstrate_relevance_scoring()

    print("\n💡 Next steps:")
    print("  • Add recency weighting for time-sensitive queries")
    print("  • Combine with importance ranking")
    print("  • Try embedding_scoring.py for better semantic matching")


if __name__ == "__main__":
    main()

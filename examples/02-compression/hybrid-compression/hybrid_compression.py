#!/usr/bin/env python3
"""
Hybrid Compression

의미적 중복 제거 + 추출형 요약을 결합하여
최고의 압축률과 품질을 달성합니다.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    calculate_cost,
    print_section,
    print_success,
    print_warning,
    visualize_comparison
)

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class HybridCompressor:
    """2단계 하이브리드 압축: 중복 제거 → 요약"""

    def __init__(
        self,
        dedup_threshold: float = 0.85,
        summary_ratio: float = 0.5
    ):
        self.dedup_threshold = dedup_threshold
        self.summary_ratio = summary_ratio

    def compress(self, documents: list[str], query: str = None) -> dict:
        """
        하이브리드 압축 수행

        Args:
            documents: 압축할 문서들
            query: 쿼리 (요약 시 관련성 가중치 사용)

        Returns:
            압축 결과 및 메트릭
        """
        # Stage 1: 의미적 중복 제거
        deduped = self._deduplicate(documents)

        # Stage 2: 추출형 요약
        if query:
            compressed = self._summarize_with_query(deduped, query)
        else:
            compressed = self._summarize(deduped)

        return {
            'original': documents,
            'after_dedup': deduped,
            'final': compressed,
            'metrics': {
                'original_count': len(documents),
                'after_dedup_count': len(deduped),
                'final_count': len(compressed),
                'original_tokens': sum(count_tokens(d) for d in documents),
                'after_dedup_tokens': sum(count_tokens(d) for d in deduped),
                'final_tokens': sum(count_tokens(d) for d in compressed),
                'dedup_reduction': 1 - len(deduped) / len(documents),
                'summary_reduction': 1 - len(compressed) / len(deduped),
                'total_reduction': 1 - len(compressed) / len(documents)
            }
        }

    def _deduplicate(self, documents: list[str]) -> list[str]:
        """의미적 중복 제거"""
        if len(documents) <= 1:
            return documents

        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)

        # 유사도 계산
        similarities = cosine_similarity(tfidf_matrix)

        # 중복 제거
        keep = []
        removed = set()

        for i in range(len(documents)):
            if i in removed:
                continue

            keep.append(documents[i])

            # 이 문서와 유사한 다른 문서들 제거
            for j in range(i + 1, len(documents)):
                if j not in removed and similarities[i][j] > self.dedup_threshold:
                    removed.add(j)

        return keep

    def _summarize(self, documents: list[str]) -> list[str]:
        """문서별 추출형 요약"""
        summarized = []

        for doc in documents:
            sentences = self._split_sentences(doc)

            if len(sentences) <= 1:
                summarized.append(doc)
                continue

            # TF-IDF 점수 계산
            vectorizer = TfidfVectorizer(stop_words='english')
            try:
                tfidf_matrix = vectorizer.fit_transform(sentences)
                scores = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
            except ValueError:
                # TF-IDF 실패 시 원문 사용
                summarized.append(doc)
                continue

            # 상위 문장 선택
            n_select = max(1, int(len(sentences) * self.summary_ratio))
            top_indices = np.argsort(scores)[-n_select:]

            # 원래 순서 유지
            top_indices = sorted(top_indices)
            summary = ' '.join([sentences[i] for i in top_indices])

            summarized.append(summary)

        return summarized

    def _summarize_with_query(self, documents: list[str], query: str) -> list[str]:
        """쿼리 관련성을 고려한 요약"""
        summarized = []

        for doc in documents:
            sentences = self._split_sentences(doc)

            if len(sentences) <= 1:
                summarized.append(doc)
                continue

            # 쿼리와 문장들 함께 벡터화
            all_texts = sentences + [query]
            vectorizer = TfidfVectorizer(stop_words='english')

            try:
                tfidf_matrix = vectorizer.fit_transform(all_texts)

                # 쿼리 벡터
                query_vector = tfidf_matrix[-1]
                sentence_vectors = tfidf_matrix[:-1]

                # 관련성 점수
                relevance_scores = cosine_similarity(sentence_vectors, query_vector).flatten()

                # 상위 문장 선택
                n_select = max(1, int(len(sentences) * self.summary_ratio))
                top_indices = np.argsort(relevance_scores)[-n_select:]

                # 원래 순서 유지
                top_indices = sorted(top_indices)
                summary = ' '.join([sentences[i] for i in top_indices])

                summarized.append(summary)
            except ValueError:
                summarized.append(doc)
                continue

        return summarized

    def _split_sentences(self, text: str) -> list[str]:
        """문장 분리"""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


def demonstrate_hybrid_compression():
    """하이브리드 압축 시연"""
    print_section("HYBRID COMPRESSION DEMO")

    # RAG 결과에서 가져온 것 같은 문서들 (중복과 중복 아닌 것 섞임)
    documents = [
        "Context engineering is a systematic approach to managing LLM context windows efficiently. It combines compression, prioritization, and dynamic assembly techniques to optimize token usage while maintaining high quality responses.",

        "Context engineering systematically manages LLM context windows for maximum efficiency. Through compression and prioritization, it optimizes token usage and maintains response quality.",

        "Token economics involves understanding the cost structure of LLM APIs. GPT-4 costs $0.03 per 1K input tokens and $0.06 per 1K output tokens. Optimization can reduce costs by 60-80%.",

        "LLM token economics focuses on API pricing and cost optimization. For example, GPT-4 charges $0.03 for input and $0.06 for output per 1K tokens. Proper techniques can save 60-80% of costs.",

        "RAG systems retrieve relevant documents from a knowledge base and use them to augment LLM prompts. The retrieval quality directly impacts the final response quality.",

        "Retrieval-Augmented Generation retrieves documents from a knowledge base to enhance LLM prompts. Better retrieval leads to better responses.",

        "Context compression reduces token count while preserving essential information. There are three main types: extractive, abstractive, and semantic compression.",

        "Dynamic context assembly builds prompts based on query type and complexity. It analyzes the query, selects an appropriate template, and allocates token budget accordingly.",

        "Context prioritization ranks information by relevance, recency, and importance. This ensures that the most valuable information fits within token limits.",

        "Production deployment requires monitoring context quality, A/B testing different strategies, and continuously optimizing based on metrics like cost, latency, and accuracy."
    ]

    query = "How does context engineering reduce LLM costs?"

    print(f"📄 Original documents: {len(documents)}")
    original_tokens = sum(count_tokens(doc) for doc in documents)
    print(f"   Total tokens: {format_tokens(original_tokens)}\n")

    print(f"🔍 Query: {query}\n")

    # 하이브리드 압축 수행
    print_section("COMPRESSION PIPELINE")

    print("Stage 1: Semantic Deduplication (threshold: 0.85)")
    print("Stage 2: Extractive Summarization (ratio: 0.5)\n")

    compressor = HybridCompressor(
        dedup_threshold=0.85,
        summary_ratio=0.5
    )

    result = compressor.compress(documents, query=query)
    metrics = result['metrics']

    # Stage 1 결과
    print_section("AFTER STAGE 1: DEDUPLICATION")
    print(f"Documents: {metrics['original_count']} → {metrics['after_dedup_count']}")
    print(f"Tokens: {format_tokens(metrics['original_tokens'])} → {format_tokens(metrics['after_dedup_tokens'])}")
    print(f"Reduction: {metrics['dedup_reduction']*100:.1f}%\n")

    if metrics['after_dedup_count'] < metrics['original_count']:
        print(f"✓ Removed {metrics['original_count'] - metrics['after_dedup_count']} duplicate documents\n")

    # Stage 2 결과
    print_section("AFTER STAGE 2: SUMMARIZATION")
    print(f"Documents: {metrics['after_dedup_count']} → {metrics['final_count']}")
    print(f"Tokens: {format_tokens(metrics['after_dedup_tokens'])} → {format_tokens(metrics['final_tokens'])}")
    print(f"Reduction: {metrics['summary_reduction']*100:.1f}%\n")

    # 최종 결과
    print_section("FINAL RESULTS")

    print(f"{'Metric':<25} {'Before':<15} {'After':<15} {'Change':<15}")
    print("-" * 70)
    print(f"{'Documents':<25} {metrics['original_count']:<15} {metrics['final_count']:<15} {-metrics['original_count']+metrics['final_count']:<15}")
    print(f"{'Total Tokens':<25} {metrics['original_tokens']:<15} {metrics['final_tokens']:<15} {-metrics['original_tokens']+metrics['final_tokens']:<15}")

    total_reduction = metrics['total_reduction']
    print(f"\n{'Total Reduction:':<25} {total_reduction*100:.1f}%")

    if total_reduction >= 0.5:
        print_success("✓ Excellent compression!")
    elif total_reduction >= 0.3:
        print_success("✓ Good compression")
    else:
        print_warning("⚠ Moderate compression")

    # 비용 분석
    print_section("COST ANALYSIS")

    model = "gpt-4"
    output_tokens = 500

    before_cost = calculate_cost(metrics['original_tokens'], output_tokens, model)
    after_cost = calculate_cost(metrics['final_tokens'], output_tokens, model)

    print(f"Model: {model}")
    print(f"Assumed output: {format_tokens(output_tokens)}\n")

    print(f"Before: ${before_cost:.4f}/query")
    print(f"After:  ${after_cost:.4f}/query")
    print(f"Savings: ${before_cost - after_cost:.4f}/query ({(1-after_cost/before_cost)*100:.1f}%)\n")

    # 월간 비용
    queries_per_month = 100_000
    monthly_savings = (before_cost - after_cost) * queries_per_month

    print(f"Monthly (at {queries_per_month:,} queries):")
    print(f"  Before: ${before_cost * queries_per_month:,.2f}")
    print(f"  After:  ${after_cost * queries_per_month:,.2f}")
    print(f"  Savings: ${monthly_savings:,.2f}")

    # 최종 압축 결과 샘플
    print_section("SAMPLE OUTPUT")

    print("First 3 compressed documents:\n")
    for i, doc in enumerate(result['final'][:3], 1):
        tokens = count_tokens(doc)
        print(f"{i}. [{format_tokens(tokens)}] {doc}\n")

    # 품질 체크
    print_section("QUALITY CHECK")

    query_keywords = set(query.lower().split())

    preserved_keywords = []
    for doc in result['final']:
        doc_words = set(doc.lower().split())
        common = query_keywords & doc_words
        preserved_keywords.extend(common)

    preserved_unique = set(preserved_keywords)
    coverage = len(preserved_unique) / len(query_keywords) if query_keywords else 0

    print(f"Query keywords: {', '.join(query_keywords)}")
    print(f"Preserved in compressed docs: {', '.join(preserved_unique)}")
    print(f"Coverage: {coverage*100:.1f}%")

    if coverage >= 0.7:
        print_success("\n✓ Good keyword preservation!")
    elif coverage >= 0.5:
        print_warning("\n⚠ Moderate keyword preservation")
    else:
        print_warning("\n⚠ Low keyword preservation - consider adjusting parameters")

    print_success("\nHybrid compression complete!")


def demonstrate_parameter_tuning():
    """파라미터 튜닝 시연"""
    print_section("PARAMETER TUNING")

    documents = [
        "Context engineering is a systematic approach to managing LLM context windows.",
        "Context engineering systematically manages LLM context windows.",
        "Token economics involves understanding LLM API costs and optimization.",
        "LLM token economics focuses on API pricing and cost optimization.",
        "RAG systems retrieve documents to augment LLM prompts.",
        "Dynamic context assembly builds prompts based on query type.",
        "Context prioritization ranks information by relevance and importance.",
        "Production deployment requires monitoring and optimization.",
    ]

    query = "What is context engineering?"

    print(f"Query: {query}")
    print(f"Original: {len(documents)} documents, {sum(count_tokens(d) for d in documents)} tokens\n")

    # 다양한 파라미터 조합 테스트
    configs = [
        {'dedup': 0.95, 'summary': 0.7, 'name': 'Conservative'},
        {'dedup': 0.85, 'summary': 0.5, 'name': 'Balanced'},
        {'dedup': 0.75, 'summary': 0.3, 'name': 'Aggressive'},
    ]

    print(f"{'Strategy':<15} {'Dedup Threshold':<20} {'Summary Ratio':<15} {'Final Docs':<12} {'Final Tokens':<12} {'Reduction':<12}")
    print("-" * 100)

    for config in configs:
        compressor = HybridCompressor(
            dedup_threshold=config['dedup'],
            summary_ratio=config['summary']
        )

        result = compressor.compress(documents, query=query)
        metrics = result['metrics']

        print(f"{config['name']:<15} {config['dedup']:<20} {config['summary']:<15} {metrics['final_count']:<12} {metrics['final_tokens']:<12} {metrics['total_reduction']*100:<11.1f}%")

    print("\n💡 Recommendations:")
    print("  • Conservative: High-stakes applications where quality is critical")
    print("  • Balanced: Most production use cases (recommended)")
    print("  • Aggressive: Cost-sensitive applications with tolerance for information loss")


def main():
    demonstrate_hybrid_compression()
    print("\n" + "="*70 + "\n")
    demonstrate_parameter_tuning()

    print("\n" + "="*70)
    print_section("BEST PRACTICES")

    print("1. Pipeline Order:")
    print("   ✓ Always deduplicate first, then summarize")
    print("   ✗ Don't summarize first - you'll lose dedup opportunities")

    print("\n2. Parameter Selection:")
    print("   • Deduplication threshold:")
    print("     - 0.95: Very strict (only near-duplicates)")
    print("     - 0.85: Balanced (recommended)")
    print("     - 0.75: Aggressive (more dedup)")
    print("   • Summary ratio:")
    print("     - 0.7: Conservative (keep most content)")
    print("     - 0.5: Balanced (recommended)")
    print("     - 0.3: Aggressive (maximum compression)")

    print("\n3. Quality Monitoring:")
    print("   • Check keyword preservation")
    print("   • Validate critical information is retained")
    print("   • A/B test compression parameters")

    print("\n4. When to Use:")
    print("   ✓ RAG results with duplicates")
    print("   ✓ Large document collections")
    print("   ✓ Cost-sensitive applications")
    print("   ✗ Already clean, unique documents")

    print("\n💡 Next steps:")
    print("  • Try different parameter combinations")
    print("  • Combine with relevance scoring")
    print("  • Monitor quality metrics in production")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Extractive Summarization for Context Compression

TF-IDF 기반 추출형 요약으로 컨텍스트를 압축합니다.
원문에서 중요한 문장을 선택하여 추출합니다.
"""

import sys
import os
import re
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    calculate_cost,
    print_section,
    print_success,
    visualize_comparison,
    get_sample_text
)


class ExtractiveSummarizer:
    """TF-IDF 기반 추출형 요약기"""

    def __init__(self, compression_ratio: float = 0.3):
        """
        Args:
            compression_ratio: 유지할 문장 비율 (0.0 ~ 1.0)
        """
        self.compression_ratio = compression_ratio

    def summarize(self, text: str, query: str = None) -> str:
        """
        텍스트를 추출형 요약으로 압축

        Args:
            text: 압축할 텍스트
            query: 쿼리 (관련성 기반 점수화에 사용)

        Returns:
            압축된 텍스트
        """
        # 문장 분리
        sentences = self._split_sentences(text)

        if not sentences:
            return text

        # 문장 점수 계산
        if query:
            scores = self._score_with_query(sentences, query)
        else:
            scores = self._score_sentences(sentences)

        # 상위 N% 문장 선택
        n_select = max(1, int(len(sentences) * self.compression_ratio))
        top_indices = np.argsort(scores)[-n_select:]
        top_indices = sorted(top_indices)  # 원래 순서 유지

        # 선택된 문장들로 재구성
        selected_sentences = [sentences[i] for i in top_indices]
        return ' '.join(selected_sentences)

    def _split_sentences(self, text: str) -> list[str]:
        """문장 분리"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _score_sentences(self, sentences: list[str]) -> np.ndarray:
        """TF-IDF 기반 문장 점수"""
        if len(sentences) == 1:
            return np.array([1.0])

        from sklearn.feature_extraction.text import TfidfVectorizer

        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(sentences)
            scores = np.asarray(tfidf_matrix.mean(axis=1)).flatten()
            return scores
        except:
            # Fallback: 문장 길이 기반
            return np.array([len(s.split()) for s in sentences], dtype=float)

    def _score_with_query(self, sentences: list[str], query: str) -> np.ndarray:
        """쿼리 관련성 기반 문장 점수"""
        if len(sentences) == 1:
            return np.array([1.0])

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            all_texts = sentences + [query]
            tfidf_matrix = vectorizer.fit_transform(all_texts)

            # 쿼리와의 유사도 계산
            query_vector = tfidf_matrix[-1]
            sentence_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(sentence_vectors, query_vector).flatten()

            return similarities
        except:
            # Fallback
            return np.array([1.0] * len(sentences))


def demonstrate_extractive_summarization():
    """추출형 요약 시연"""
    print_section("EXTRACTIVE SUMMARIZATION DEMO")

    # 샘플 텍스트
    text = get_sample_text("large")
    query = "What is context engineering and why is it important?"

    original_tokens = count_tokens(text)

    print(f"Original text: {format_tokens(original_tokens)}")
    print(f"Query: {query}")
    print(f"\nFirst 200 characters:")
    print(f"{text[:200]}...\n")

    # 다양한 압축 비율 테스트
    compression_ratios = [0.5, 0.3, 0.2]

    results = []

    for ratio in compression_ratios:
        print(f"{'─'*60}")
        print(f"Compression Ratio: {ratio:.0%}")
        print(f"{'─'*60}")

        # 압축
        summarizer = ExtractiveSummarizer(compression_ratio=ratio)
        compressed = summarizer.summarize(text, query)
        compressed_tokens = count_tokens(compressed)

        # 통계
        reduction = (original_tokens - compressed_tokens) / original_tokens
        print(f"  Compressed: {format_tokens(compressed_tokens)}")
        print(f"  Reduction: {reduction:.1%}")
        print(f"  Preview: {compressed[:150]}...\n")

        results.append({
            'ratio': ratio,
            'tokens': compressed_tokens,
            'reduction': reduction,
            'compressed': compressed
        })

    # 비교 분석
    print_section("COMPRESSION COMPARISON")

    print(f"{'Ratio':<12} {'Tokens':<15} {'Reduction':<15} {'Cost/Query':<15}")
    print(f"{'-'*60}")

    for result in results:
        cost = calculate_cost(result['tokens'], output_tokens=500)
        print(f"{result['ratio']:.0%:<12} {result['tokens']:<15} {result['reduction']:.1%:<15} ${cost:<14.4f}")

    # 품질 vs 압축 트레이드오프
    print_section("QUALITY VS COMPRESSION TRADE-OFF")

    print("압축률이 높을수록:")
    print("  ✓ 토큰 수 감소 (비용 절감)")
    print("  ✓ 처리 속도 향상")
    print("  ✗ 정보 손실 가능")

    print("\n권장사항:")
    print("  • 50% 압축: 안전한 시작점, 대부분의 정보 보존")
    print("  • 30% 압축: 균형잡힌 선택, 핵심 정보 유지")
    print("  • 20% 압축: 공격적 압축, 가장 중요한 정보만")

    # 실전 예제
    print_section("PRODUCTION EXAMPLE")

    # 30% 압축 사용
    summarizer = ExtractiveSummarizer(compression_ratio=0.3)
    compressed = summarizer.summarize(text, query)
    compressed_tokens = count_tokens(compressed)

    cost_before = calculate_cost(original_tokens, 500)
    cost_after = calculate_cost(compressed_tokens, 500)
    savings = cost_before - cost_after

    visualize_comparison(
        before={'tokens': original_tokens, 'cost_per_query': cost_before},
        after={'tokens': compressed_tokens, 'cost_per_query': cost_after}
    )

    print("Monthly Savings (100K queries):")
    monthly_savings = savings * 100000
    print(f"  ${monthly_savings:,.2f}\n")

    print_success("Extractive summarization complete!")


def main():
    demonstrate_extractive_summarization()

    print("\n💡 Next steps:")
    print("  • Try different compression ratios")
    print("  • Compare with gpt_summary.py (abstractive)")
    print("  • Use hybrid_compression.py for best results")


if __name__ == "__main__":
    main()

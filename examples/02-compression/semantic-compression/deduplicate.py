#!/usr/bin/env python3
"""
Semantic Deduplication for Context Compression

의미적으로 유사하거나 중복된 내용을 제거하여
컨텍스트를 압축합니다.
"""

import sys
import os
import re
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    print_section,
    print_success,
    print_warning,
    visualize_comparison,
    get_sample_text
)


class SemanticDeduplicator:
    """의미적 중복 제거기"""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)
        """
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, documents: list[str]) -> list[str]:
        """
        문서에서 중복 제거

        Args:
            documents: 문서 리스트

        Returns:
            중복이 제거된 문서 리스트
        """
        if not documents:
            return []

        # 1. 완전 중복 제거 (빠른 체크)
        unique_docs = self._remove_exact_duplicates(documents)

        # 2. 의미적 중복 제거
        deduped = self._remove_semantic_duplicates(unique_docs)

        return deduped

    def _remove_exact_duplicates(self, documents: list[str]) -> list[str]:
        """완전히 동일한 문서 제거"""
        seen = set()
        unique = []

        for doc in documents:
            # 정규화 (공백, 대소문자)
            normalized = ' '.join(doc.lower().split())
            if normalized not in seen:
                seen.add(normalized)
                unique.append(doc)

        return unique

    def _remove_semantic_duplicates(self, documents: list[str]) -> list[str]:
        """의미적으로 유사한 문서 제거"""
        if len(documents) <= 1:
            return documents

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            # TF-IDF 벡터화
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform(documents)

            # 유사도 매트릭스
            similarity_matrix = cosine_similarity(vectors)

            # 중복 그룹 찾기
            kept = []
            removed_indices = set()

            for i in range(len(documents)):
                if i in removed_indices:
                    continue

                kept.append(documents[i])

                # i와 유사한 문서들 찾기
                for j in range(i + 1, len(documents)):
                    if j not in removed_indices:
                        if similarity_matrix[i][j] > self.similarity_threshold:
                            removed_indices.add(j)

            return kept

        except:
            # Fallback: 간단한 문자열 기반 중복 제거
            return self._simple_dedup(documents)

    def _simple_dedup(self, documents: list[str]) -> list[str]:
        """간단한 중복 제거 (fallback)"""
        unique = []
        seen_words = []

        for doc in documents:
            words = set(doc.lower().split())

            # 50% 이상 단어가 겹치면 중복으로 간주
            is_duplicate = False
            for seen in seen_words:
                overlap = len(words & seen) / len(words | seen)
                if overlap > 0.5:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(doc)
                seen_words.append(words)

        return unique


def demonstrate_deduplication():
    """중복 제거 시연"""
    print_section("SEMANTIC DEDUPLICATION DEMO")

    # 중복이 있는 문서 세트 생성
    documents = [
        "Context engineering is a systematic approach to managing LLM context windows efficiently.",
        "Context engineering systematically manages LLM context windows for efficiency.",  # 유사
        "Token economics is about understanding and optimizing LLM costs.",
        "Context engineering is a systematic approach to managing LLM context windows efficiently.",  # 완전 중복
        "RAG retrieves relevant documents from a knowledge base.",
        "Understanding LLM costs and optimizing token usage is token economics.",  # 유사
        "Context windows have limited capacity in tokens.",
        "The context window size varies by model, from 4K to 1M tokens.",
        "Context engineering includes compression, prioritization, and dynamic assembly.",
        "RAG systems retrieve documents from knowledge bases.",  # 유사
    ]

    print(f"Original documents: {len(documents)}")
    print(f"\nSample documents:")
    for i, doc in enumerate(documents[:3], 1):
        print(f"  {i}. {doc}")
    print(f"  ... and {len(documents) - 3} more\n")

    # 토큰 계산
    original_tokens = sum(count_tokens(doc) for doc in documents)
    print(f"Original total: {format_tokens(original_tokens)}\n")

    # 중복 제거
    print("⏳ Removing duplicates...")

    deduplicator = SemanticDeduplicator(similarity_threshold=0.85)
    deduped_docs = deduplicator.deduplicate(documents)

    deduped_tokens = sum(count_tokens(doc) for doc in deduped_docs)

    print_success(f"Removed {len(documents) - len(deduped_docs)} duplicate documents!\n")

    # 결과 표시
    print_section("DEDUPLICATED DOCUMENTS")

    for i, doc in enumerate(deduped_docs, 1):
        tokens = count_tokens(doc)
        print(f"{i}. [{tokens} tokens] {doc}")

    print()

    # 통계
    reduction = (original_tokens - deduped_tokens) / original_tokens

    visualize_comparison(
        before={'documents': len(documents), 'tokens': original_tokens},
        after={'documents': len(deduped_docs), 'tokens': deduped_tokens}
    )

    print(f"Documents removed: {len(documents) - len(deduped_docs)}")
    print(f"Token reduction: {reduction:.1%}")

    # 임계값 실험
    print_section("SIMILARITY THRESHOLD EXPERIMENT")

    thresholds = [0.95, 0.85, 0.75, 0.65]

    print(f"{'Threshold':<12} {'Kept Docs':<12} {'Tokens':<12} {'Reduction':<12}")
    print(f"{'-'*50}")

    for threshold in thresholds:
        dedup = SemanticDeduplicator(similarity_threshold=threshold)
        result = dedup.deduplicate(documents)
        tokens = sum(count_tokens(doc) for doc in result)
        reduction = (original_tokens - tokens) / original_tokens

        print(f"{threshold:<12.2f} {len(result):<12} {tokens:<12} {reduction:<12.1%}")

    print("\n권장사항:")
    print("  • 0.95: 거의 동일한 것만 제거 (보수적)")
    print("  • 0.85: 유사한 것 제거 (권장)")
    print("  • 0.75: 다소 유사한 것도 제거 (공격적)")
    print("  • 0.65: 관련 있으면 제거 (매우 공격적, 주의)")

    # 실전 시나리오
    print_section("PRODUCTION SCENARIO")

    print("RAG 시스템에서:")
    print("  1. 벡터 검색으로 20개 문서 검색")
    print("  2. 의미적 중복 제거 (threshold=0.85)")
    print("  3. 결과: 평균 12-15개 문서 (40% 중복 제거)")
    print("  4. 토큰 절감: 30-40%")
    print("  5. 품질: 거의 동일 (중복 정보 제거로 오히려 명확)")

    from shared.utils import calculate_cost

    # 비용 계산
    cost_before = calculate_cost(original_tokens, 500)
    cost_after = calculate_cost(deduped_tokens, 500)
    savings = cost_before - cost_after

    print(f"\n💰 Cost Savings:")
    print(f"  Before: ${cost_before:.4f} per query")
    print(f"  After: ${cost_after:.4f} per query")
    print(f"  Savings: ${savings:.4f} per query")
    print(f"  Monthly (100K): ${savings * 100000:,.2f}")

    print_success("\nDeduplication complete!")


def main():
    demonstrate_deduplication()

    print("\n💡 Key Takeaways:")
    print("  1. Remove exact duplicates first (fast)")
    print("  2. Then remove semantic duplicates (slower but effective)")
    print("  3. Adjust threshold based on use case")
    print("  4. Typical reduction: 30-40% for RAG results")


if __name__ == "__main__":
    main()

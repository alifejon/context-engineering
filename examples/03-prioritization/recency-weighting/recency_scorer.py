#!/usr/bin/env python3
"""
Recency-Based Weighting

시간 기반 점수 가중치를 적용하여
최신 정보를 우선시합니다.
"""

import sys
import os
from datetime import datetime, timedelta

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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RecencyScorer:
    """관련성 + 최신성 결합 점수화"""

    def __init__(
        self,
        relevance_weight: float = 0.6,
        recency_weight: float = 0.4,
        decay_days: float = 30.0
    ):
        """
        Args:
            relevance_weight: 관련성 가중치 (0-1)
            recency_weight: 최신성 가중치 (0-1)
            decay_days: 반감기 (일 단위)
        """
        self.relevance_weight = relevance_weight
        self.recency_weight = recency_weight
        self.decay_days = decay_days

    def score_documents(
        self,
        documents: list[dict],
        query: str,
        current_time: datetime = None
    ) -> list[dict]:
        """
        문서들에 관련성 + 최신성 점수 부여

        Args:
            documents: [{'content': str, 'timestamp': datetime}, ...]
            query: 검색 쿼리
            current_time: 현재 시간 (기본: 현재)

        Returns:
            점수가 포함된 문서 리스트
        """
        if current_time is None:
            current_time = datetime.now()

        # 관련성 점수 계산
        contents = [doc['content'] for doc in documents]
        relevance_scores = self._calculate_relevance(contents, query)

        # 최신성 점수 계산
        recency_scores = [
            self._calculate_recency(doc['timestamp'], current_time)
            for doc in documents
        ]

        # 결합 점수
        scored_docs = []
        for i, doc in enumerate(documents):
            final_score = (
                relevance_scores[i] * self.relevance_weight +
                recency_scores[i] * self.recency_weight
            )

            scored_docs.append({
                'index': i,
                'content': doc['content'],
                'timestamp': doc['timestamp'],
                'relevance_score': float(relevance_scores[i]),
                'recency_score': float(recency_scores[i]),
                'final_score': float(final_score),
                'tokens': count_tokens(doc['content'])
            })

        # 최종 점수 순으로 정렬
        scored_docs.sort(key=lambda x: x['final_score'], reverse=True)

        return scored_docs

    def _calculate_relevance(self, documents: list[str], query: str) -> np.ndarray:
        """TF-IDF 기반 관련성 계산"""
        vectorizer = TfidfVectorizer(stop_words='english')
        all_texts = documents + [query]
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        query_vector = tfidf_matrix[-1]
        doc_vectors = tfidf_matrix[:-1]

        similarities = cosine_similarity(doc_vectors, query_vector).flatten()
        return similarities

    def _calculate_recency(self, doc_time: datetime, current_time: datetime) -> float:
        """
        지수 감쇠 기반 최신성 점수

        Score = exp(-age_days / decay_days)
        """
        age = current_time - doc_time
        age_days = age.total_seconds() / (24 * 3600)

        # 지수 감쇠
        recency_score = np.exp(-age_days / self.decay_days)

        return recency_score


def demonstrate_recency_scoring():
    """최신성 점수화 시연"""
    print_section("RECENCY-BASED SCORING DEMO")

    # 현재 시간
    current_time = datetime.now()

    # 다양한 시점의 문서들
    documents = [
        {
            'content': 'GPT-4 Turbo released with 128K context window and lower pricing.',
            'timestamp': current_time - timedelta(days=2)
        },
        {
            'content': 'OpenAI announces GPT-4 with 8K and 32K context windows.',
            'timestamp': current_time - timedelta(days=365)
        },
        {
            'content': 'New study shows context compression reduces costs by 70%.',
            'timestamp': current_time - timedelta(days=7)
        },
        {
            'content': 'Context engineering best practices guide published.',
            'timestamp': current_time - timedelta(days=180)
        },
        {
            'content': 'GPT-4 Turbo pricing updated: $0.01 input, $0.03 output.',
            'timestamp': current_time - timedelta(days=1)
        },
        {
            'content': 'RAG systems improve response quality with context optimization.',
            'timestamp': current_time - timedelta(days=90)
        },
        {
            'content': 'Token economics fundamentals for LLM applications.',
            'timestamp': current_time - timedelta(days=270)
        },
        {
            'content': 'Latest benchmark: GPT-4 Turbo vs Claude 3 performance.',
            'timestamp': current_time - timedelta(days=5)
        },
    ]

    query = "What are the latest GPT-4 pricing and features?"

    print(f"Query: {query}\n")
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M')}\n")
    print(f"Documents: {len(documents)}\n")

    # 최신성 점수화
    print("⏳ Calculating relevance + recency scores...\n")

    scorer = RecencyScorer(
        relevance_weight=0.6,
        recency_weight=0.4,
        decay_days=30.0
    )

    scored_docs = scorer.score_documents(documents, query, current_time)

    print_success("Scoring complete!\n")

    # 결과 표시
    print_section("SCORED DOCUMENTS")

    print(f"{'Rank':<6} {'Relevance':<12} {'Recency':<12} {'Final':<12} {'Age':<15} {'Preview':<40}")
    print("-" * 100)

    for i, doc in enumerate(scored_docs, 1):
        age = current_time - doc['timestamp']
        age_days = age.total_seconds() / (24 * 3600)

        if age_days < 7:
            age_str = f"{age_days:.0f} days"
        elif age_days < 30:
            age_str = f"{age_days/7:.0f} weeks"
        else:
            age_str = f"{age_days/30:.0f} months"

        preview = doc['content'][:37] + "..." if len(doc['content']) > 40 else doc['content']

        # 색상: 최신 = 초록, 오래된 = 빨강
        if age_days < 7:
            color = '\033[92m'  # Green
        elif age_days < 30:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'

        print(f"{i:<6} {doc['relevance_score']:<12.3f} {color}{doc['recency_score']:<12.3f}{reset} {doc['final_score']:<12.3f} {color}{age_str:<15}{reset} {preview}")

    # 가중치 비교
    print_section("WEIGHT COMPARISON")

    print("Testing different weight configurations:\n")

    configs = [
        {'rel': 1.0, 'rec': 0.0, 'name': 'Relevance Only'},
        {'rel': 0.7, 'rec': 0.3, 'name': 'Favor Relevance'},
        {'rel': 0.5, 'rec': 0.5, 'name': 'Balanced'},
        {'rel': 0.3, 'rec': 0.7, 'name': 'Favor Recency'},
        {'rel': 0.0, 'rec': 1.0, 'name': 'Recency Only'},
    ]

    print(f"{'Configuration':<20} {'Top Document Preview':<60}")
    print("-" * 85)

    for config in configs:
        scorer_test = RecencyScorer(
            relevance_weight=config['rel'],
            recency_weight=config['rec'],
            decay_days=30.0
        )

        scored_test = scorer_test.score_documents(documents, query, current_time)
        top_doc = scored_test[0]
        preview = top_doc['content'][:57] + "..." if len(top_doc['content']) > 60 else top_doc['content']

        print(f"{config['name']:<20} {preview}")

    # 시간 감쇠 시각화
    print_section("RECENCY DECAY VISUALIZATION")

    print(f"Decay period: {scorer.decay_days} days\n")
    print(f"{'Age (days)':<15} {'Recency Score':<20} {'Visualization'}")
    print("-" * 60)

    test_ages = [0, 1, 7, 14, 30, 60, 90, 180, 365]

    for age_days in test_ages:
        recency = np.exp(-age_days / scorer.decay_days)
        bar = "█" * int(recency * 30)

        if recency > 0.7:
            color = '\033[92m'  # Green
        elif recency > 0.3:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'

        print(f"{age_days:<15} {color}{recency:<20.3f}{reset} {color}{bar}{reset}")


def demonstrate_use_cases():
    """사용 사례별 권장 설정"""
    print_section("USE CASE RECOMMENDATIONS")

    use_cases = [
        {
            'name': 'News Search',
            'description': 'Breaking news, current events',
            'relevance': 0.3,
            'recency': 0.7,
            'decay_days': 7,
            'rationale': 'Freshness is critical, older news loses value quickly'
        },
        {
            'name': 'Tech Documentation',
            'description': 'API docs, framework guides',
            'relevance': 0.6,
            'recency': 0.4,
            'decay_days': 90,
            'rationale': 'Relevance matters most, but prefer recent versions'
        },
        {
            'name': 'Academic Research',
            'description': 'Scientific papers, studies',
            'relevance': 0.7,
            'recency': 0.3,
            'decay_days': 365,
            'rationale': 'Quality over freshness, but consider recent findings'
        },
        {
            'name': 'Product Updates',
            'description': 'Release notes, changelogs',
            'relevance': 0.4,
            'recency': 0.6,
            'decay_days': 30,
            'rationale': 'Recent updates most relevant, old ones less useful'
        },
        {
            'name': 'General Knowledge',
            'description': 'Encyclopedia, definitions',
            'relevance': 0.9,
            'recency': 0.1,
            'decay_days': 730,
            'rationale': 'Facts don\'t change, relevance is key'
        },
    ]

    for uc in use_cases:
        print(f"\n{uc['name']}")
        print(f"  Use: {uc['description']}")
        print(f"  Weights: Relevance {uc['relevance']*100:.0f}% / Recency {uc['recency']*100:.0f}%")
        print(f"  Decay: {uc['decay_days']} days")
        print(f"  Why: {uc['rationale']}")


def demonstrate_production_example():
    """프로덕션 예제"""
    print_section("PRODUCTION EXAMPLE")

    print("Example: Tech news aggregator\n")

    print("```python")
    print("class NewsSearchSystem:")
    print("    def __init__(self):")
    print("        self.scorer = RecencyScorer(")
    print("            relevance_weight=0.3,")
    print("            recency_weight=0.7,")
    print("            decay_days=7  # News becomes stale quickly")
    print("        )")
    print("")
    print("    def search(self, query: str) -> list:")
    print("        # 1. Retrieve candidate documents")
    print("        candidates = self.vector_db.search(query, k=50)")
    print("")
    print("        # 2. Score with recency weighting")
    print("        scored = self.scorer.score_documents(")
    print("            candidates,")
    print("            query,")
    print("            current_time=datetime.now()")
    print("        )")
    print("")
    print("        # 3. Select top K within budget")
    print("        selected = self.select_top_k(")
    print("            scored,")
    print("            k=5,")
    print("            max_tokens=4000")
    print("        )")
    print("")
    print("        return selected")
    print("```")


def main():
    demonstrate_recency_scoring()
    print("\n" + "="*70 + "\n")
    demonstrate_use_cases()
    print("\n" + "="*70 + "\n")
    demonstrate_production_example()

    print("\n" + "="*70)
    print_section("BEST PRACTICES")

    print("1. Weight Selection:")
    print("   • Time-sensitive content: Higher recency weight (0.6-0.8)")
    print("   • Stable content: Higher relevance weight (0.7-0.9)")
    print("   • General purpose: Balanced (0.5/0.5)")

    print("\n2. Decay Period:")
    print("   • News/events: Short (3-7 days)")
    print("   • Tech docs: Medium (30-90 days)")
    print("   • General knowledge: Long (365+ days)")

    print("\n3. Implementation:")
    print("   • Store timestamps with all documents")
    print("   • Update scores periodically (not every query)")
    print("   • Consider timezone handling")
    print("   • Cache computed scores")

    print("\n4. Quality Control:")
    print("   • Monitor distribution of document ages")
    print("   • Validate that recent docs are surfacing")
    print("   • A/B test different decay periods")
    print("   • Collect user feedback on recency")

    print("\n💡 Next steps:")
    print("  • Combine with importance ranking")
    print("  • Add source credibility weights")
    print("  • Implement dynamic weight adjustment")
    print("  • Try different decay functions (linear, step)")


if __name__ == "__main__":
    main()

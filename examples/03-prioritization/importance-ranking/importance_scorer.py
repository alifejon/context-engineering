#!/usr/bin/env python3
"""
Importance-Based Ranking

문서의 신뢰도, 구체성, 구조적 품질 등을
종합하여 중요도 점수를 계산합니다.
"""

import sys
import os
import re

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


class ImportanceScorer:
    """다차원 중요도 점수화"""

    def __init__(
        self,
        relevance_weight: float = 0.4,
        credibility_weight: float = 0.2,
        specificity_weight: float = 0.2,
        structure_weight: float = 0.2
    ):
        """
        Args:
            relevance_weight: 관련성 가중치
            credibility_weight: 신뢰도 가중치
            specificity_weight: 구체성 가중치
            structure_weight: 구조 품질 가중치
        """
        self.relevance_weight = relevance_weight
        self.credibility_weight = credibility_weight
        self.specificity_weight = specificity_weight
        self.structure_weight = structure_weight

    def score_documents(
        self,
        documents: list[dict],
        query: str
    ) -> list[dict]:
        """
        문서들에 종합 중요도 점수 부여

        Args:
            documents: [{'content': str, 'source': str, ...}, ...]
            query: 검색 쿼리

        Returns:
            점수가 포함된 문서 리스트
        """
        contents = [doc['content'] for doc in documents]

        # 각 차원별 점수 계산
        relevance_scores = self._calculate_relevance(contents, query)
        credibility_scores = [self._calculate_credibility(doc) for doc in documents]
        specificity_scores = [self._calculate_specificity(doc['content']) for doc in documents]
        structure_scores = [self._calculate_structure_quality(doc['content']) for doc in documents]

        # 결합 점수
        scored_docs = []
        for i, doc in enumerate(documents):
            final_score = (
                relevance_scores[i] * self.relevance_weight +
                credibility_scores[i] * self.credibility_weight +
                specificity_scores[i] * self.specificity_weight +
                structure_scores[i] * self.structure_weight
            )

            scored_docs.append({
                'index': i,
                'content': doc['content'],
                'source': doc.get('source', 'unknown'),
                'relevance_score': float(relevance_scores[i]),
                'credibility_score': float(credibility_scores[i]),
                'specificity_score': float(specificity_scores[i]),
                'structure_score': float(structure_scores[i]),
                'final_score': float(final_score),
                'tokens': count_tokens(doc['content'])
            })

        # 최종 점수 순으로 정렬
        scored_docs.sort(key=lambda x: x['final_score'], reverse=True)

        return scored_docs

    def _calculate_relevance(self, documents: list[str], query: str) -> np.ndarray:
        """TF-IDF 기반 관련성"""
        vectorizer = TfidfVectorizer(stop_words='english')
        all_texts = documents + [query]
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        query_vector = tfidf_matrix[-1]
        doc_vectors = tfidf_matrix[:-1]

        similarities = cosine_similarity(doc_vectors, query_vector).flatten()
        return similarities

    def _calculate_credibility(self, doc: dict) -> float:
        """
        출처 기반 신뢰도 점수

        신뢰도 계층:
        - Official docs: 1.0
        - Academic papers: 0.9
        - Industry blogs: 0.7
        - Community forums: 0.5
        - Unknown: 0.5
        """
        source = doc.get('source', 'unknown').lower()

        credibility_map = {
            'official': 1.0,
            'documentation': 1.0,
            'docs': 1.0,
            'academic': 0.9,
            'paper': 0.9,
            'journal': 0.9,
            'blog': 0.7,
            'medium': 0.7,
            'stackoverflow': 0.6,
            'reddit': 0.5,
            'forum': 0.5,
            'unknown': 0.5
        }

        # 출처에서 키워드 찾기
        for keyword, score in credibility_map.items():
            if keyword in source:
                return score

        return 0.5  # 기본값

    def _calculate_specificity(self, text: str) -> float:
        """
        구체성 점수

        구체적인 문서 특징:
        - 숫자/통계 포함
        - 코드 예제 포함
        - 구체적인 고유명사
        - 단계별 설명
        """
        score = 0.0

        # 숫자 포함 (0-0.3)
        numbers = re.findall(r'\d+', text)
        number_density = len(numbers) / len(text.split())
        score += min(number_density * 10, 0.3)

        # 코드 블록 또는 기술적 기호 (0-0.3)
        code_indicators = ['()', '{}', '[]', '```', 'def ', 'class ', 'function', 'import']
        code_count = sum(1 for indicator in code_indicators if indicator in text)
        score += min(code_count * 0.1, 0.3)

        # 구체적인 예제 표현 (0-0.2)
        example_phrases = ['for example', 'e.g.', 'such as', 'like', 'specifically']
        example_count = sum(1 for phrase in example_phrases if phrase.lower() in text.lower())
        score += min(example_count * 0.1, 0.2)

        # 단계별 설명 (0-0.2)
        step_indicators = re.findall(r'\b(step|first|second|third|finally|then)\b', text.lower())
        score += min(len(step_indicators) * 0.05, 0.2)

        return min(score, 1.0)

    def _calculate_structure_quality(self, text: str) -> float:
        """
        구조적 품질 점수

        좋은 구조:
        - 적절한 문장 길이
        - 단락 구성
        - 완결된 문장
        - 가독성
        """
        score = 0.0

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # 문장 수 (너무 적지도 많지도 않게) (0-0.3)
        num_sentences = len(sentences)
        if 3 <= num_sentences <= 10:
            score += 0.3
        elif 2 <= num_sentences <= 15:
            score += 0.2
        else:
            score += 0.1

        # 평균 문장 길이 (0-0.3)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if 10 <= avg_sentence_length <= 25:  # 이상적 범위
            score += 0.3
        elif 5 <= avg_sentence_length <= 35:
            score += 0.2
        else:
            score += 0.1

        # 문장 완결성 (마침표로 끝남) (0-0.2)
        if text.strip().endswith(('.', '!', '?')):
            score += 0.2

        # 대문자로 시작 (0-0.2)
        proper_start = sum(1 for s in sentences if s and s[0].isupper())
        score += (proper_start / len(sentences)) * 0.2

        return min(score, 1.0)


def demonstrate_importance_scoring():
    """중요도 점수화 시연"""
    print_section("IMPORTANCE-BASED SCORING DEMO")

    documents = [
        {
            'content': 'Context engineering optimizes LLM costs by 60-80% through compression. For example, extractive summarization can reduce tokens by 50% while maintaining quality. Steps: 1) Analyze content 2) Select important sentences 3) Reconstruct context.',
            'source': 'official documentation'
        },
        {
            'content': 'llm optimization is important',
            'source': 'unknown'
        },
        {
            'content': 'According to recent studies, proper context management significantly reduces API costs. Research from Stanford shows compression ratios of 3:1 are achievable.',
            'source': 'academic paper'
        },
        {
            'content': 'I think context engineering is useful. It helps with costs. You should try it.',
            'source': 'reddit'
        },
        {
            'content': 'Token economics: GPT-4 costs $0.03/1K input tokens. With 100K queries/month at 5K tokens each, monthly cost is $15,000. Context compression to 2K tokens reduces this to $6,000.',
            'source': 'blog'
        },
        {
            'content': 'Context window management involves various techniques including sliding windows, token budgeting, and priority-based selection strategies',
            'source': 'unknown'
        },
        {
            'content': 'The implementation uses Python with tiktoken library. Code example: encoding = tiktoken.get_encoding("cl100k_base"); tokens = encoding.encode(text); return len(tokens)',
            'source': 'documentation'
        },
        {
            'content': 'Many developers face challenges with LLM costs',
            'source': 'forum'
        },
    ]

    query = "How to optimize LLM costs with context engineering?"

    print(f"Query: {query}\n")
    print(f"Documents to score: {len(documents)}\n")

    # 중요도 점수화
    print("⏳ Calculating importance scores...\n")

    scorer = ImportanceScorer(
        relevance_weight=0.4,
        credibility_weight=0.2,
        specificity_weight=0.2,
        structure_weight=0.2
    )

    scored_docs = scorer.score_documents(documents, query)

    print_success("Scoring complete!\n")

    # 결과 표시
    print_section("IMPORTANCE SCORES")

    print(f"{'Rank':<6} {'Final':<8} {'Rel':<7} {'Cred':<7} {'Spec':<7} {'Struc':<7} {'Source':<15} {'Preview':<30}")
    print("-" * 100)

    for i, doc in enumerate(scored_docs, 1):
        preview = doc['content'][:27] + "..." if len(doc['content']) > 30 else doc['content']

        # 색상: 높은 점수 = 초록
        if doc['final_score'] > 0.6:
            color = '\033[92m'  # Green
        elif doc['final_score'] > 0.4:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'

        print(f"{i:<6} {color}{doc['final_score']:<8.3f}{reset} "
              f"{doc['relevance_score']:<7.2f} "
              f"{doc['credibility_score']:<7.2f} "
              f"{doc['specificity_score']:<7.2f} "
              f"{doc['structure_score']:<7.2f} "
              f"{doc['source']:<15} {preview}")

    # 상위 문서 상세 분석
    print_section("TOP 3 DOCUMENTS ANALYSIS")

    for i, doc in enumerate(scored_docs[:3], 1):
        print(f"\n{i}. Final Score: {doc['final_score']:.3f}")
        print(f"   Content: {doc['content']}")
        print(f"   Source: {doc['source']}")
        print(f"   Breakdown:")
        print(f"     • Relevance:   {doc['relevance_score']:.3f} (weight: {scorer.relevance_weight})")
        print(f"     • Credibility: {doc['credibility_score']:.3f} (weight: {scorer.credibility_weight})")
        print(f"     • Specificity: {doc['specificity_score']:.3f} (weight: {scorer.specificity_weight})")
        print(f"     • Structure:   {doc['structure_score']:.3f} (weight: {scorer.structure_weight})")


def demonstrate_weight_strategies():
    """다양한 가중치 전략 시연"""
    print_section("WEIGHT STRATEGIES BY USE CASE")

    strategies = [
        {
            'name': 'Factual QA',
            'weights': {'rel': 0.3, 'cred': 0.4, 'spec': 0.2, 'struc': 0.1},
            'rationale': 'Credibility is critical for facts'
        },
        {
            'name': 'How-to Tutorials',
            'weights': {'rel': 0.4, 'cred': 0.2, 'spec': 0.3, 'struc': 0.1},
            'rationale': 'Need relevant, specific instructions'
        },
        {
            'name': 'Research',
            'weights': {'rel': 0.4, 'cred': 0.3, 'spec': 0.2, 'struc': 0.1},
            'rationale': 'Balance relevance and source quality'
        },
        {
            'name': 'Code Examples',
            'weights': {'rel': 0.3, 'cred': 0.1, 'spec': 0.5, 'struc': 0.1},
            'rationale': 'Specific code examples are most valuable'
        },
        {
            'name': 'General Knowledge',
            'weights': {'rel': 0.5, 'cred': 0.2, 'spec': 0.1, 'struc': 0.2},
            'rationale': 'Relevance and readability matter most'
        },
    ]

    print(f"{'Use Case':<20} {'Relevance':<12} {'Credibility':<15} {'Specificity':<15} {'Structure':<12} {'Rationale'}")
    print("-" * 100)

    for strategy in strategies:
        w = strategy['weights']
        print(f"{strategy['name']:<20} {w['rel']*100:<11.0f}% {w['cred']*100:<14.0f}% "
              f"{w['spec']*100:<14.0f}% {w['struc']*100:<11.0f}% {strategy['rationale']}")


def demonstrate_production_pipeline():
    """프로덕션 파이프라인 예제"""
    print_section("PRODUCTION PIPELINE")

    print("Complete scoring pipeline combining all dimensions:\n")

    print("```python")
    print("class ProductionScorer:")
    print("    def __init__(self):")
    print("        # Multiple scorers for different dimensions")
    print("        self.relevance_scorer = TFIDFScorer()")
    print("        self.recency_scorer = RecencyScorer()")
    print("        self.importance_scorer = ImportanceScorer()")
    print("")
    print("    def score_documents(self, docs: list, query: str) -> list:")
    print("        # 1. Relevance scoring")
    print("        rel_scored = self.relevance_scorer.score(docs, query)")
    print("")
    print("        # 2. Add recency weights")
    print("        rec_scored = self.recency_scorer.add_weights(rel_scored)")
    print("")
    print("        # 3. Add importance signals")
    print("        final_scored = self.importance_scorer.add_weights(rec_scored)")
    print("")
    print("        # 4. Final ranking")
    print("        return sorted(final_scored, key=lambda x: x['score'])")
    print("")
    print("# Usage")
    print("scorer = ProductionScorer()")
    print("results = scorer.score_documents(documents, query)")
    print("top_10 = results[:10]")
    print("```")


def main():
    demonstrate_importance_scoring()
    print("\n" + "="*70 + "\n")
    demonstrate_weight_strategies()
    print("\n" + "="*70 + "\n")
    demonstrate_production_pipeline()

    print("\n" + "="*70)
    print_section("BEST PRACTICES")

    print("1. Dimension Selection:")
    print("   • Always include relevance")
    print("   • Add credibility for factual domains")
    print("   • Add specificity for technical content")
    print("   • Add recency for time-sensitive queries")

    print("\n2. Weight Tuning:")
    print("   • Start with balanced weights (0.25 each)")
    print("   • Adjust based on use case")
    print("   • A/B test different configurations")
    print("   • Monitor user engagement metrics")

    print("\n3. Credibility Sources:")
    print("   • Maintain a trusted source whitelist")
    print("   • Update credibility scores over time")
    print("   • Consider domain-specific authority")
    print("   • Allow manual overrides")

    print("\n4. Quality Signals:")
    print("   • Specificity: numbers, examples, code")
    print("   • Structure: sentence length, completeness")
    print("   • Engagement: clicks, dwell time")
    print("   • Freshness: publication date, update frequency")

    print("\n5. Production Considerations:")
    print("   • Cache computed scores")
    print("   • Batch score calculations")
    print("   • Monitor score distributions")
    print("   • Log decisions for analysis")

    print("\n💡 Next steps:")
    print("  • Combine with relevance and recency scoring")
    print("  • Add user feedback signals")
    print("  • Implement learning-to-rank")
    print("  • Build comprehensive scoring pipeline")


if __name__ == "__main__":
    main()

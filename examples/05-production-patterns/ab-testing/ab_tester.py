#!/usr/bin/env python3
"""
A/B Testing for Context Strategies

다양한 컨텍스트 전략을 비교 테스트하여
최적의 설정을 찾습니다.
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Callable
from datetime import datetime
import random

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    calculate_cost,
    print_section,
    print_success,
    print_warning
)


@dataclass
class Strategy:
    """컨텍스트 전략"""
    name: str
    description: str
    process_func: Callable
    params: dict


@dataclass
class TestResult:
    """A/B 테스트 결과"""
    strategy_name: str
    query: str
    context_before: str
    context_after: str
    tokens_before: int
    tokens_after: int
    cost_before: float
    cost_after: float
    quality_score: float
    latency_ms: float
    timestamp: datetime


class ABTester:
    """A/B 테스트 프레임워크"""

    def __init__(self, strategies: List[Strategy]):
        self.strategies = strategies
        self.results: Dict[str, List[TestResult]] = {s.name: [] for s in strategies}

    def run_test(
        self,
        queries: List[str],
        contexts: List[str],
        traffic_split: Dict[str, float] = None
    ):
        """
        A/B 테스트 실행

        Args:
            queries: 테스트 쿼리들
            contexts: 원본 컨텍스트들
            traffic_split: 전략별 트래픽 비율 (기본: 균등 분배)
        """
        if traffic_split is None:
            # 균등 분배
            split = 1.0 / len(self.strategies)
            traffic_split = {s.name: split for s in self.strategies}

        # 각 쿼리를 전략에 할당
        for query, context in zip(queries, contexts):
            # 트래픽 분배에 따라 전략 선택
            strategy = self._select_strategy(traffic_split)

            # 전략 적용
            result = self._apply_strategy(strategy, query, context)
            self.results[strategy.name].append(result)

    def _select_strategy(self, traffic_split: Dict[str, float]) -> Strategy:
        """트래픽 분배에 따라 전략 선택"""
        rand = random.random()
        cumulative = 0

        for strategy in self.strategies:
            cumulative += traffic_split[strategy.name]
            if rand <= cumulative:
                return strategy

        return self.strategies[-1]

    def _apply_strategy(
        self,
        strategy: Strategy,
        query: str,
        context: str
    ) -> TestResult:
        """전략 적용 및 결과 측정"""
        start_time = datetime.now()

        # 전략 적용
        processed_context = strategy.process_func(context, query, **strategy.params)

        # 메트릭 계산
        tokens_before = count_tokens(context)
        tokens_after = count_tokens(processed_context)

        model = strategy.params.get('model', 'gpt-4-turbo')
        cost_before = calculate_cost(tokens_before, 500, model)
        cost_after = calculate_cost(tokens_after, 500, model)

        # 품질 점수 시뮬레이션 (실제로는 LLM 호출 또는 사용자 피드백)
        quality_score = self._simulate_quality_score(
            strategy.name,
            tokens_before,
            tokens_after
        )

        latency = (datetime.now() - start_time).total_seconds() * 1000

        return TestResult(
            strategy_name=strategy.name,
            query=query,
            context_before=context,
            context_after=processed_context,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            cost_before=cost_before,
            cost_after=cost_after,
            quality_score=quality_score,
            latency_ms=latency,
            timestamp=start_time
        )

    def _simulate_quality_score(
        self,
        strategy_name: str,
        tokens_before: int,
        tokens_after: int
    ) -> float:
        """품질 점수 시뮬레이션"""
        compression_ratio = tokens_after / tokens_before if tokens_before > 0 else 1.0

        # 기본 품질 (전략별)
        base_quality = {
            'baseline': 1.0,
            'aggressive_compression': 0.75,
            'moderate_compression': 0.88,
            'conservative_compression': 0.95,
            'smart_selection': 0.92
        }.get(strategy_name, 0.85)

        # 압축률에 따른 품질 저하
        if compression_ratio < 0.3:
            quality_penalty = 0.15
        elif compression_ratio < 0.5:
            quality_penalty = 0.08
        elif compression_ratio < 0.7:
            quality_penalty = 0.03
        else:
            quality_penalty = 0.0

        return max(0.5, base_quality - quality_penalty + random.uniform(-0.05, 0.05))

    def analyze_results(self) -> dict:
        """결과 분석"""
        analysis = {}

        for strategy_name, results in self.results.items():
            if not results:
                continue

            # 평균 메트릭 계산
            avg_cost_before = sum(r.cost_before for r in results) / len(results)
            avg_cost_after = sum(r.cost_after for r in results) / len(results)
            avg_quality = sum(r.quality_score for r in results) / len(results)
            avg_compression = sum(r.tokens_after / r.tokens_before for r in results) / len(results)
            avg_latency = sum(r.latency_ms for r in results) / len(results)

            analysis[strategy_name] = {
                'sample_size': len(results),
                'avg_cost_before': avg_cost_before,
                'avg_cost_after': avg_cost_after,
                'cost_savings': avg_cost_before - avg_cost_after,
                'cost_savings_pct': (1 - avg_cost_after / avg_cost_before) * 100 if avg_cost_before > 0 else 0,
                'avg_quality': avg_quality,
                'avg_compression_ratio': avg_compression,
                'avg_latency_ms': avg_latency,
                'efficiency_score': self._calculate_efficiency(avg_cost_after, avg_quality, avg_latency)
            }

        return analysis

    def _calculate_efficiency(self, cost: float, quality: float, latency: float) -> float:
        """효율성 점수 계산 (높을수록 좋음)"""
        # 정규화된 메트릭 결합
        cost_score = max(0, 1 - cost / 0.05)  # $0.05를 기준으로 정규화
        quality_score = quality
        latency_score = max(0, 1 - latency / 3000)  # 3000ms를 기준으로 정규화

        # 가중 평균
        return (cost_score * 0.4 + quality_score * 0.4 + latency_score * 0.2)

    def get_winner(self) -> str:
        """최고 성능 전략 선택"""
        analysis = self.analyze_results()

        if not analysis:
            return None

        # 효율성 점수 기준
        return max(analysis.items(), key=lambda x: x[1]['efficiency_score'])[0]


# 전략 함수들
def baseline_strategy(context: str, query: str, **params) -> str:
    """베이스라인: 변경 없음"""
    return context


def aggressive_compression(context: str, query: str, **params) -> str:
    """공격적 압축: 30% 유지"""
    target_ratio = 0.3
    sentences = context.split('. ')
    target_count = max(1, int(len(sentences) * target_ratio))
    return '. '.join(sentences[:target_count]) + '.'


def moderate_compression(context: str, query: str, **params) -> str:
    """적당한 압축: 60% 유지"""
    target_ratio = 0.6
    sentences = context.split('. ')
    target_count = max(1, int(len(sentences) * target_ratio))
    return '. '.join(sentences[:target_count]) + '.'


def conservative_compression(context: str, query: str, **params) -> str:
    """보수적 압축: 80% 유지"""
    target_ratio = 0.8
    sentences = context.split('. ')
    target_count = max(1, int(len(sentences) * target_ratio))
    return '. '.join(sentences[:target_count]) + '.'


def smart_selection(context: str, query: str, **params) -> str:
    """스마트 선택: 쿼리 관련 문장 우선"""
    sentences = context.split('. ')
    query_words = set(query.lower().split())

    # 관련성 점수 계산
    scored = []
    for sent in sentences:
        sent_words = set(sent.lower().split())
        relevance = len(query_words & sent_words) / len(query_words) if query_words else 0
        scored.append((sent, relevance))

    # 관련성 높은 순으로 정렬 후 60% 선택
    scored.sort(key=lambda x: x[1], reverse=True)
    target_count = max(1, int(len(scored) * 0.6))
    selected = [s[0] for s in scored[:target_count]]

    return '. '.join(selected) + '.'


def demonstrate_ab_testing():
    """A/B 테스팅 시연"""
    print_section("A/B TESTING DEMO")

    # 전략 정의
    strategies = [
        Strategy(
            name='baseline',
            description='No compression (control group)',
            process_func=baseline_strategy,
            params={'model': 'gpt-4-turbo'}
        ),
        Strategy(
            name='aggressive_compression',
            description='30% of content retained',
            process_func=aggressive_compression,
            params={'model': 'gpt-4-turbo'}
        ),
        Strategy(
            name='moderate_compression',
            description='60% of content retained',
            process_func=moderate_compression,
            params={'model': 'gpt-4-turbo'}
        ),
        Strategy(
            name='conservative_compression',
            description='80% of content retained',
            process_func=conservative_compression,
            params={'model': 'gpt-4-turbo'}
        ),
        Strategy(
            name='smart_selection',
            description='Query-aware 60% selection',
            process_func=smart_selection,
            params={'model': 'gpt-4-turbo'}
        ),
    ]

    print(f"Testing {len(strategies)} strategies:\n")
    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy.name}: {strategy.description}")

    # 테스트 데이터
    test_queries = [
        "What is context engineering?",
        "How to reduce LLM costs?",
        "Explain compression techniques",
        "What are the benefits of caching?",
        "How to implement RAG?",
    ] * 4  # 각 쿼리 4번씩 = 20개 샘플

    test_context = """
Context engineering is a systematic approach to managing LLM context windows efficiently.
It involves compression, prioritization, and dynamic assembly techniques.
Token economics plays a crucial role in cost optimization.
Context compression can reduce costs by 60-80% while maintaining quality.
Semantic deduplication removes redundant information.
Extractive summarization selects key sentences.
RAG systems benefit greatly from context optimization.
Caching frequently used contexts saves significant costs.
Dynamic assembly adapts context based on query complexity.
Quality monitoring ensures optimal performance.
"""

    test_contexts = [test_context] * len(test_queries)

    # A/B 테스트 실행
    print(f"\n⏳ Running A/B test on {len(test_queries)} queries...")

    tester = ABTester(strategies)

    # 균등 트래픽 분배
    traffic_split = {s.name: 1.0 / len(strategies) for s in strategies}

    tester.run_test(test_queries, test_contexts, traffic_split)

    print_success("✓ Test complete!\n")

    # 결과 분석
    print_section("TEST RESULTS")

    analysis = tester.analyze_results()

    # 테이블 형식으로 출력
    print(f"{'Strategy':<25} {'Samples':<10} {'Avg Cost':<12} {'Savings':<12} {'Quality':<10} {'Latency':<12} {'Efficiency':<12}")
    print("-" * 110)

    for strategy_name, metrics in sorted(analysis.items(), key=lambda x: x[1]['efficiency_score'], reverse=True):
        print(f"{strategy_name:<25} {metrics['sample_size']:<10} "
              f"${metrics['avg_cost_after']:<11.4f} "
              f"{metrics['cost_savings_pct']:<11.1f}% "
              f"{metrics['avg_quality']:<10.2f} "
              f"{metrics['avg_latency_ms']:<11.0f}ms "
              f"{metrics['efficiency_score']:<12.2f}")

    # 승자 발표
    winner = tester.get_winner()
    print(f"\n🏆 Winner: {winner}")

    winner_metrics = analysis[winner]
    print(f"\n  • Cost savings: {winner_metrics['cost_savings_pct']:.1f}%")
    print(f"  • Quality score: {winner_metrics['avg_quality']:.2f}")
    print(f"  • Efficiency: {winner_metrics['efficiency_score']:.2f}")

    # 상세 비교
    print_section("DETAILED COMPARISON")

    baseline_metrics = analysis.get('baseline', None)
    if baseline_metrics:
        print("Compared to baseline:\n")

        for strategy_name, metrics in analysis.items():
            if strategy_name == 'baseline':
                continue

            cost_improvement = (baseline_metrics['avg_cost_after'] - metrics['avg_cost_after']) / baseline_metrics['avg_cost_after'] * 100
            quality_change = (metrics['avg_quality'] - baseline_metrics['avg_quality']) / baseline_metrics['avg_quality'] * 100

            print(f"{strategy_name}:")
            print(f"  Cost: {cost_improvement:+.1f}%")
            print(f"  Quality: {quality_change:+.1f}%")
            print(f"  Compression: {(1 - metrics['avg_compression_ratio']) * 100:.0f}%")
            print()


def demonstrate_statistical_significance():
    """통계적 유의성 예시"""
    print_section("STATISTICAL SIGNIFICANCE")

    print("For production A/B tests, ensure statistical significance:\n")

    print("Sample Size Calculator:")
    print("```python")
    print("from scipy import stats")
    print("")
    print("def calculate_sample_size(")
    print("    baseline_rate: float,")
    print("    minimum_detectable_effect: float,")
    print("    alpha: float = 0.05,")
    print("    power: float = 0.8")
    print(") -> int:")
    print("    \"\"\"Calculate required sample size\"\"\"")
    print("    effect_size = minimum_detectable_effect / baseline_rate")
    print("    ")
    print("    # Cohen's h for proportions")
    print("    h = 2 * (arcsin(sqrt(baseline_rate)) - ")
    print("          arcsin(sqrt(baseline_rate * (1 + effect_size))))")
    print("    ")
    print("    # Sample size per group")
    print("    n = (stats.norm.ppf(1 - alpha/2) + stats.norm.ppf(power))**2 / h**2")
    print("    return int(n) * 2  # Total for both groups")
    print("```\n")

    print("Example calculations:\n")

    examples = [
        {'baseline': 0.85, 'mde': 0.02, 'alpha': 0.05, 'power': 0.8},
        {'baseline': 0.75, 'mde': 0.05, 'alpha': 0.05, 'power': 0.8},
        {'baseline': 0.90, 'mde': 0.01, 'alpha': 0.05, 'power': 0.8},
    ]

    print(f"{'Baseline':<12} {'MDE':<12} {'Alpha':<12} {'Power':<12} {'Sample Size':<15}")
    print("-" * 70)

    for ex in examples:
        # 간단한 추정 (실제로는 scipy 사용)
        estimated_size = int(1000 / (ex['mde'] / ex['baseline']) ** 2)
        print(f"{ex['baseline']:<12} {ex['mde']:<12} {ex['alpha']:<12} {ex['power']:<12} ~{estimated_size:<15}")

    print("\n💡 Recommendations:")
    print("  • Run tests for at least 1-2 weeks")
    print("  • Ensure sufficient sample size")
    print("  • Check for day-of-week effects")
    print("  • Monitor for novelty effects")


def main():
    demonstrate_ab_testing()
    print("\n" + "="*70 + "\n")
    demonstrate_statistical_significance()

    print("\n" + "="*70)
    print_section("A/B TESTING BEST PRACTICES")

    print("1. Test Design:")
    print("   • Define clear hypothesis")
    print("   • Choose primary metric (cost, quality, or composite)")
    print("   • Calculate required sample size")
    print("   • Set test duration")

    print("\n2. Traffic Allocation:")
    print("   • Start with small % for new strategy (10-20%)")
    print("   • Gradually increase if showing promise")
    print("   • Keep control group throughout")
    print("   • Use consistent hashing for user assignment")

    print("\n3. Metrics to Track:")
    print("   • Primary: Cost savings, quality score")
    print("   • Secondary: Latency, cache hit rate")
    print("   • Guardrail: Error rate, user satisfaction")
    print("   • Long-term: Retention, engagement")

    print("\n4. Decision Criteria:")
    print("   • Statistical significance (p < 0.05)")
    print("   • Practical significance (>5% improvement)")
    print("   • No degradation in guardrail metrics")
    print("   • Consistent results across segments")

    print("\n5. Rollout Strategy:")
    print("   • Start: 10% test, 90% control")
    print("   • Week 1: Monitor closely")
    print("   • Week 2: Increase to 50% if positive")
    print("   • Week 3: Full rollout or iterate")

    print("\n6. Common Pitfalls:")
    print("   ✗ Sample size too small")
    print("   ✗ Stopping test too early")
    print("   ✗ P-hacking (multiple testing)")
    print("   ✗ Ignoring seasonality")
    print("   ✗ Not accounting for novelty effect")

    print("\n💡 Next steps:")
    print("  • Set up A/B testing infrastructure")
    print("  • Define key metrics and targets")
    print("  • Create experiment tracking system")
    print("  • Run first experiment!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Production Cost Optimization

프로덕션 환경에서 LLM 비용을 최적화하는
실전 전략들을 구현합니다.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

try:
    from examples.shared.utils import (
        count_tokens,
        calculate_cost,
        print_section,
        print_success,
    )

    from examples.production_ready.core.error_handling import (
        validate_input,
        ValidationError,
        OptimizationError,
        TokenCountingError,
        with_retry,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for direct script execution
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from examples.shared.utils import (
        count_tokens,
        calculate_cost,
        print_section,
        print_success,
    )

    from examples.production_ready.core.error_handling import (
        validate_input,
        ValidationError,
        OptimizationError,
        TokenCountingError,
        with_retry,
    )


@dataclass
class ModelConfig:
    """모델 설정"""
    name: str
    max_tokens: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    quality_score: float  # 0-1


class CostOptimizer:
    """비용 최적화 전략 관리자"""

    # 모델 설정
    MODELS = {
        'gpt-4': ModelConfig('gpt-4', 8192, 0.03, 0.06, 1.0),
        'gpt-4-turbo': ModelConfig('gpt-4-turbo', 128000, 0.01, 0.03, 0.95),
        'gpt-3.5-turbo': ModelConfig('gpt-3.5-turbo', 16385, 0.0015, 0.002, 0.75),
    }

    def __init__(self):
        self.cache = {}
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0,
            'total_cost': 0.0,
            'savings': 0.0
        }

    def optimize_query(
        self,
        query: str,
        context: str,
        min_quality: float = 0.8,
        max_cost: float = None
    ) -> dict:
        """
        쿼리 최적화 수행

        Args:
            query: 사용자 쿼리
            context: 컨텍스트
            min_quality: 최소 품질 요구사항
            max_cost: 최대 비용

        Returns:
            최적화 결과
        """
        try:
            query, context = validate_input(query, context, min_quality, max_cost)
        except ValidationError as exc:
            raise OptimizationError(f"Invalid optimization inputs: {exc}") from exc

        self.metrics['total_queries'] += 1

        # 1. 캐시 확인
        cache_result = self._check_cache(query, context)
        if cache_result:
            self.metrics['cache_hits'] += 1
            self.metrics['savings'] += cache_result['saved_cost']
            return cache_result

        self.metrics['cache_misses'] += 1

        # 2. 최적 모델 선택
        model = self._select_model(query, context, min_quality, max_cost)

        # 3. 컨텍스트 최적화
        optimized_context = self._optimize_context(context, model)

        # 4. 비용 계산
        input_tokens = self._count_tokens(query + optimized_context, model.name)
        estimated_output = 500  # 예상 출력
        cost = self._calculate_cost(input_tokens, estimated_output, model.name)

        self.metrics['total_cost'] += cost

        result = {
            'model': model.name,
            'original_context_tokens': self._count_tokens(context, model.name),
            'optimized_context_tokens': self._count_tokens(optimized_context, model.name),
            'total_input_tokens': input_tokens,
            'estimated_output_tokens': estimated_output,
            'estimated_cost': cost,
            'quality_score': model.quality_score,
            'optimized_context': optimized_context,
            'cached': False
        }

        # 캐시에 저장
        self._cache_result(query, context, result)

        return result

    def _check_cache(self, query: str, context: str) -> Optional[dict]:
        """캐시 확인"""
        cache_key = self._get_cache_key(query, context)

        if cache_key in self.cache:
            cached = self.cache[cache_key]

            # 캐시 유효성 확인 (1시간)
            if datetime.now() - cached['timestamp'] < timedelta(hours=1):
                result = cached['result'].copy()
                result['cached'] = True
                result['saved_cost'] = result['estimated_cost']
                result['estimated_cost'] = 0.0  # 캐시된 요청은 무료
                return result

            # 만료된 캐시 제거
            del self.cache[cache_key]

        return None

    def _cache_result(self, query: str, context: str, result: dict):
        """결과 캐싱"""
        cache_key = self._get_cache_key(query, context)
        self.cache[cache_key] = {
            'timestamp': datetime.now(),
            'result': result
        }

    def _get_cache_key(self, query: str, context: str) -> str:
        """캐시 키 생성"""
        # 간단한 구현: 실제로는 해시 사용
        return f"{query[:50]}:{context[:100]}"

    def _select_model(
        self,
        query: str,
        context: str,
        min_quality: float,
        max_cost: Optional[float]
    ) -> ModelConfig:
        """
        최적 모델 선택

        전략:
        1. 품질 요구사항 충족하는 모델들 필터링
        2. 그 중 가장 저렴한 모델 선택
        3. 비용 제한 고려
        """
        # 쿼리 복잡도 분석
        complexity = self._analyze_complexity(query, context)

        # 품질 요구사항 충족 모델
        candidates = [
            model for model in self.MODELS.values()
            if model.quality_score >= min_quality
        ]

        if not candidates:
            # 품질 요구사항 완화
            candidates = [max(self.MODELS.values(), key=lambda m: m.quality_score)]

        # 비용 기반 선택
        if max_cost:
            # 비용 제한 내에서 최고 품질
            affordable = []
            for model in candidates:
                input_tokens = self._count_tokens(query + context, model.name)
                cost = self._calculate_cost(input_tokens, 500, model.name)
                if cost <= max_cost:
                    affordable.append((model, cost))

            if affordable:
                return max(affordable, key=lambda x: x[0].quality_score)[0]

        # 복잡도에 따른 모델 선택
        if complexity == 'simple':
            # 간단한 쿼리 → 가장 저렴한 모델
            return min(candidates, key=lambda m: m.input_cost_per_1k)
        elif complexity == 'complex':
            # 복잡한 쿼리 → 가장 높은 품질
            return max(candidates, key=lambda m: m.quality_score)
        else:
            # 중간 복잡도 → 균형잡힌 선택
            return self.MODELS['gpt-4-turbo']

    def _analyze_complexity(self, query: str, context: str) -> str:
        """쿼리 복잡도 분석"""
        query_tokens = count_tokens(query)
        context_tokens = count_tokens(context)

        # 간단한 휴리스틱
        if query_tokens < 20 and context_tokens < 1000:
            return 'simple'
        elif query_tokens > 50 or context_tokens > 5000:
            return 'complex'
        else:
            return 'medium'

    def _optimize_context(self, context: str, model: ModelConfig) -> str:
        """
        모델에 맞게 컨텍스트 최적화

        전략:
        - 저품질 모델 → 더 많은 컨텍스트 (명확성 보완)
        - 고품질 모델 → 압축된 컨텍스트 (비용 절감)
        """
        tokens = self._count_tokens(context, model.name)

        if model.quality_score >= 0.9:
            # 고품질 모델: 공격적 압축 가능
            target_ratio = 0.6
        elif model.quality_score >= 0.8:
            # 중품질 모델: 적당한 압축
            target_ratio = 0.8
        else:
            # 저품질 모델: 최소 압축
            target_ratio = 0.9

        target_tokens = int(tokens * target_ratio)

        # 간단한 압축 (실제로는 더 정교한 방법 사용)
        if tokens > target_tokens:
            # 문장 단위로 자르기
            sentences = context.split('. ')
            compressed = []
            current_tokens = 0

            for sentence in sentences:
                sentence_tokens = self._count_tokens(sentence, model.name)
                if current_tokens + sentence_tokens <= target_tokens:
                    compressed.append(sentence)
                    current_tokens += sentence_tokens
                else:
                    break

            return '. '.join(compressed) + '.'

        return context

    def get_metrics(self) -> dict:
        """메트릭 반환"""
        cache_hit_rate = 0
        if self.metrics['total_queries'] > 0:
            cache_hit_rate = self.metrics['cache_hits'] / self.metrics['total_queries']

        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate,
            'avg_cost_per_query': self.metrics['total_cost'] / max(1, self.metrics['total_queries'])
        }

    @with_retry(max_attempts=3, backoff_factor=2.0, exceptions=(Exception,))
    def _count_tokens(self, text: str, model: str) -> int:
        """Safely count tokens with retry handling."""
        try:
            return count_tokens(text, model)
        except Exception as exc:  # pragma: no cover - defensive
            raise TokenCountingError(f"Failed to count tokens for model {model}") from exc

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Wrapper to calculate cost with clear intent."""
        try:
            return calculate_cost(input_tokens, output_tokens, model)
        except Exception as exc:  # pragma: no cover - defensive
            raise OptimizationError(f"Failed to calculate cost for {model}") from exc


def demonstrate_cost_optimization():
    """비용 최적화 시연"""
    print_section("PRODUCTION COST OPTIMIZATION")

    optimizer = CostOptimizer()

    # 다양한 쿼리 시나리오
    scenarios = [
        {
            'name': 'Simple Factual Query',
            'query': 'What is context engineering?',
            'context': 'Context engineering is a systematic approach to managing LLM context windows.',
            'min_quality': 0.7,
            'max_cost': None
        },
        {
            'name': 'Complex Analysis',
            'query': 'Analyze the tradeoffs between different compression algorithms and provide detailed recommendations.',
            'context': '''
Context compression techniques include extractive summarization, semantic deduplication, and hybrid approaches.
Extractive summarization selects important sentences using TF-IDF scoring.
Semantic deduplication removes similar documents using cosine similarity.
Hybrid compression combines both methods for maximum efficiency.
Each method has different tradeoffs in terms of compression ratio, quality preservation, and computational cost.
            ''',
            'min_quality': 0.9,
            'max_cost': None
        },
        {
            'name': 'Budget-Constrained',
            'query': 'Summarize the key points',
            'context': 'LLM cost optimization strategies include context compression, model selection, and caching. ' * 20,
            'min_quality': 0.75,
            'max_cost': 0.01
        },
        {
            'name': 'Cached Query (Repeat)',
            'query': 'What is context engineering?',
            'context': 'Context engineering is a systematic approach to managing LLM context windows.',
            'min_quality': 0.7,
            'max_cost': None
        },
    ]

    print("Processing 4 queries with different requirements:\n")

    results = []
    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"Scenario: {scenario['name']}")
        print(f"Query: {scenario['query']}")
        print(f"Min Quality: {scenario['min_quality']}")
        if scenario['max_cost']:
            print(f"Max Cost: ${scenario['max_cost']}")

        result = optimizer.optimize_query(
            scenario['query'],
            scenario['context'],
            scenario['min_quality'],
            scenario['max_cost']
        )

        results.append(result)

        print(f"\n✓ Selected Model: {result['model']}")
        print(f"  Quality Score: {result['quality_score']}")
        print(f"  Context: {result['original_context_tokens']} → {result['optimized_context_tokens']} tokens")
        print(f"  Estimated Cost: ${result['estimated_cost']:.4f}")

        if result['cached']:
            print(f"  ⚡ Cached! Saved: ${result['saved_cost']:.4f}")

    # 전체 메트릭
    print("\n" + "="*70)
    print_section("OPTIMIZATION METRICS")

    metrics = optimizer.get_metrics()

    print(f"Total Queries: {metrics['total_queries']}")
    print(f"Cache Hits: {metrics['cache_hits']}")
    print(f"Cache Misses: {metrics['cache_misses']}")
    print(f"Cache Hit Rate: {metrics['cache_hit_rate']*100:.1f}%")
    print(f"\nTotal Cost: ${metrics['total_cost']:.4f}")
    print(f"Total Savings: ${metrics['savings']:.4f}")
    print(f"Average Cost/Query: ${metrics['avg_cost_per_query']:.4f}")

    # 비교 분석
    print_section("COST COMPARISON")

    print("Without optimization (always GPT-4):\n")

    baseline_cost = 0
    for i, scenario in enumerate(scenarios):
        input_tokens = count_tokens(scenario['query'] + scenario['context'], 'gpt-4')
        cost = calculate_cost(input_tokens, 500, 'gpt-4')
        baseline_cost += cost
        print(f"  Scenario {i+1}: ${cost:.4f}")

    print(f"\nTotal baseline cost: ${baseline_cost:.4f}")
    print(f"Optimized cost: ${metrics['total_cost']:.4f}")
    print(f"Savings: ${baseline_cost - metrics['total_cost']:.4f} ({(1 - metrics['total_cost']/baseline_cost)*100:.1f}%)")

    if (baseline_cost - metrics['total_cost']) / baseline_cost > 0.5:
        print_success("\n✓ Excellent optimization! >50% savings")


def demonstrate_strategies():
    """최적화 전략 설명"""
    print_section("OPTIMIZATION STRATEGIES")

    strategies = [
        {
            'name': '1. Smart Model Routing',
            'description': 'Route queries to appropriate models based on complexity',
            'savings': '40-60%',
            'implementation': [
                'Analyze query complexity',
                'Match to model capabilities',
                'Consider quality requirements',
                'Balance cost vs quality'
            ]
        },
        {
            'name': '2. Aggressive Caching',
            'description': 'Cache results for repeated or similar queries',
            'savings': '80-95% (for cache hits)',
            'implementation': [
                'Hash query + context',
                'Set appropriate TTL',
                'Handle cache invalidation',
                'Monitor hit rates'
            ]
        },
        {
            'name': '3. Context Compression',
            'description': 'Reduce context size while preserving quality',
            'savings': '50-70%',
            'implementation': [
                'Semantic deduplication',
                'Extractive summarization',
                'Priority-based selection',
                'Adaptive compression ratios'
            ]
        },
        {
            'name': '4. Batch Processing',
            'description': 'Process multiple queries together',
            'savings': '20-30%',
            'implementation': [
                'Group similar queries',
                'Share context across batch',
                'Amortize fixed costs',
                'Use async processing'
            ]
        },
        {
            'name': '5. Token Budget Management',
            'description': 'Strict token limits per query type',
            'savings': '30-50%',
            'implementation': [
                'Set per-query budgets',
                'Enforce limits',
                'Monitor overages',
                'Adjust dynamically'
            ]
        },
    ]

    for strategy in strategies:
        print(f"\n{strategy['name']}")
        print(f"  {strategy['description']}")
        print(f"  Potential savings: {strategy['savings']}")
        print(f"  Implementation:")
        for step in strategy['implementation']:
            print(f"    • {step}")


def main():
    demonstrate_cost_optimization()
    print("\n" + "="*70 + "\n")
    demonstrate_strategies()

    print("\n" + "="*70)
    print_section("PRODUCTION CHECKLIST")

    print("✓ Model Selection:")
    print("  • Define quality requirements per use case")
    print("  • Create model routing logic")
    print("  • Monitor quality metrics")
    print("  • Adjust routing based on feedback")

    print("\n✓ Caching:")
    print("  • Implement cache layer (Redis, Memcached)")
    print("  • Set appropriate TTLs")
    print("  • Monitor hit rates (target: >60%)")
    print("  • Implement cache warming for common queries")

    print("\n✓ Context Optimization:")
    print("  • Implement compression pipeline")
    print("  • A/B test compression ratios")
    print("  • Monitor quality impact")
    print("  • Tune per query type")

    print("\n✓ Monitoring:")
    print("  • Track cost per query")
    print("  • Monitor model distribution")
    print("  • Alert on cost anomalies")
    print("  • Weekly cost reviews")

    print("\n✓ Continuous Improvement:")
    print("  • Collect user feedback")
    print("  • Analyze failure cases")
    print("  • Test new strategies")
    print("  • Update routing rules")

    print("\n💡 Next steps:")
    print("  • Implement context monitoring")
    print("  • Set up A/B testing framework")
    print("  • Build cost alert system")
    print("  • Create optimization dashboard")


if __name__ == "__main__":
    main()

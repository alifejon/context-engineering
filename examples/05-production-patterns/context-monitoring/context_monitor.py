#!/usr/bin/env python3
"""
Context Quality Monitoring

프로덕션 환경에서 컨텍스트 품질과 성능을
실시간으로 모니터링합니다.
"""

import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

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
class ContextMetrics:
    """컨텍스트 메트릭"""
    timestamp: datetime
    query: str
    context_tokens: int
    response_tokens: int
    total_cost: float
    latency_ms: float
    quality_score: Optional[float] = None
    cache_hit: bool = False
    model: str = 'gpt-4'
    compression_ratio: Optional[float] = None


@dataclass
class MonitoringAlert:
    """모니터링 알람"""
    level: str  # INFO, WARNING, CRITICAL
    category: str  # cost, quality, latency, tokens
    message: str
    timestamp: datetime
    value: float
    threshold: float


class ContextMonitor:
    """컨텍스트 모니터링 시스템"""

    def __init__(
        self,
        cost_threshold_hourly: float = 10.0,
        latency_threshold_ms: float = 3000,
        quality_threshold: float = 0.7,
        token_threshold: int = 10000
    ):
        self.metrics: List[ContextMetrics] = []
        self.alerts: List[MonitoringAlert] = []

        # 임계값
        self.cost_threshold_hourly = cost_threshold_hourly
        self.latency_threshold_ms = latency_threshold_ms
        self.quality_threshold = quality_threshold
        self.token_threshold = token_threshold

    def log_request(self, metrics: ContextMetrics):
        """요청 메트릭 기록"""
        self.metrics.append(metrics)
        self._check_thresholds(metrics)

    def _check_thresholds(self, metrics: ContextMetrics):
        """임계값 체크 및 알람 생성"""
        # 비용 체크
        hourly_cost = self._calculate_hourly_cost()
        if hourly_cost > self.cost_threshold_hourly:
            self.alerts.append(MonitoringAlert(
                level='WARNING',
                category='cost',
                message=f'Hourly cost ${hourly_cost:.2f} exceeds threshold ${self.cost_threshold_hourly:.2f}',
                timestamp=datetime.now(),
                value=hourly_cost,
                threshold=self.cost_threshold_hourly
            ))

        # 지연시간 체크
        if metrics.latency_ms > self.latency_threshold_ms:
            self.alerts.append(MonitoringAlert(
                level='WARNING',
                category='latency',
                message=f'High latency: {metrics.latency_ms:.0f}ms (threshold: {self.latency_threshold_ms:.0f}ms)',
                timestamp=datetime.now(),
                value=metrics.latency_ms,
                threshold=self.latency_threshold_ms
            ))

        # 품질 체크
        if metrics.quality_score and metrics.quality_score < self.quality_threshold:
            self.alerts.append(MonitoringAlert(
                level='CRITICAL',
                category='quality',
                message=f'Low quality score: {metrics.quality_score:.2f} (threshold: {self.quality_threshold:.2f})',
                timestamp=datetime.now(),
                value=metrics.quality_score,
                threshold=self.quality_threshold
            ))

        # 토큰 체크
        if metrics.context_tokens > self.token_threshold:
            self.alerts.append(MonitoringAlert(
                level='INFO',
                category='tokens',
                message=f'Large context: {metrics.context_tokens} tokens (threshold: {self.token_threshold})',
                timestamp=datetime.now(),
                value=metrics.context_tokens,
                threshold=self.token_threshold
            ))

    def _calculate_hourly_cost(self) -> float:
        """지난 1시간 비용 계산"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        recent_metrics = [
            m for m in self.metrics
            if m.timestamp > hour_ago
        ]

        return sum(m.total_cost for m in recent_metrics)

    def get_dashboard(self) -> dict:
        """대시보드 데이터 생성"""
        if not self.metrics:
            return {
                'total_requests': 0,
                'total_cost': 0,
                'avg_latency_ms': 0,
                'avg_tokens': 0,
                'cache_hit_rate': 0,
                'alerts': []
            }

        total_requests = len(self.metrics)
        total_cost = sum(m.total_cost for m in self.metrics)
        avg_latency = sum(m.latency_ms for m in self.metrics) / total_requests
        avg_tokens = sum(m.context_tokens for m in self.metrics) / total_requests

        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        cache_hit_rate = cache_hits / total_requests

        # 품질 점수 평균 (있는 것만)
        quality_scores = [m.quality_score for m in self.metrics if m.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        # 모델 분포
        model_counts = defaultdict(int)
        for m in self.metrics:
            model_counts[m.model] += 1

        # 시간대별 비용
        hourly_costs = self._calculate_hourly_breakdown()

        # 최근 알람
        recent_alerts = sorted(self.alerts, key=lambda a: a.timestamp, reverse=True)[:10]

        return {
            'total_requests': total_requests,
            'total_cost': total_cost,
            'avg_latency_ms': avg_latency,
            'avg_tokens': avg_tokens,
            'avg_quality': avg_quality,
            'cache_hit_rate': cache_hit_rate,
            'model_distribution': dict(model_counts),
            'hourly_costs': hourly_costs,
            'recent_alerts': recent_alerts,
            'alert_count': len(self.alerts)
        }

    def _calculate_hourly_breakdown(self) -> List[Dict]:
        """시간대별 비용 분해"""
        if not self.metrics:
            return []

        # 최근 24시간을 1시간 단위로 분할
        now = datetime.now()
        hourly_data = []

        for hour in range(24):
            start_time = now - timedelta(hours=hour+1)
            end_time = now - timedelta(hours=hour)

            hour_metrics = [
                m for m in self.metrics
                if start_time <= m.timestamp < end_time
            ]

            if hour_metrics:
                hourly_data.append({
                    'hour': start_time.strftime('%H:00'),
                    'requests': len(hour_metrics),
                    'cost': sum(m.total_cost for m in hour_metrics),
                    'avg_latency': sum(m.latency_ms for m in hour_metrics) / len(hour_metrics)
                })

        return list(reversed(hourly_data))

    def get_recommendations(self) -> List[str]:
        """최적화 권장사항 생성"""
        recommendations = []
        dashboard = self.get_dashboard()

        # 비용 권장사항
        if dashboard['total_cost'] > 0:
            hourly_rate = dashboard['total_cost'] / max(1, len(dashboard['hourly_costs']))
            if hourly_rate > 5:
                recommendations.append(
                    f"💰 High cost rate (${hourly_rate:.2f}/hr). Consider:\n"
                    "  • Implementing caching\n"
                    "  • Using context compression\n"
                    "  • Routing to cheaper models"
                )

        # 캐시 권장사항
        if dashboard['cache_hit_rate'] < 0.4:
            recommendations.append(
                f"⚡ Low cache hit rate ({dashboard['cache_hit_rate']*100:.0f}%). Consider:\n"
                "  • Implementing query similarity matching\n"
                "  • Increasing cache TTL\n"
                "  • Pre-warming cache for common queries"
            )

        # 토큰 권장사항
        if dashboard['avg_tokens'] > 5000:
            recommendations.append(
                f"📊 High average tokens ({dashboard['avg_tokens']:.0f}). Consider:\n"
                "  • Implementing context compression\n"
                "  • Using semantic deduplication\n"
                "  • Setting stricter token budgets"
            )

        # 지연시간 권장사항
        if dashboard['avg_latency_ms'] > 2000:
            recommendations.append(
                f"⏱️ High latency ({dashboard['avg_latency_ms']:.0f}ms). Consider:\n"
                "  • Reducing context size\n"
                "  • Using faster models\n"
                "  • Implementing async processing"
            )

        # 품질 권장사항
        if dashboard['avg_quality'] and dashboard['avg_quality'] < 0.8:
            recommendations.append(
                f"⚠️ Low quality score ({dashboard['avg_quality']:.2f}). Consider:\n"
                "  • Using higher quality models\n"
                "  • Reducing compression ratios\n"
                "  • Improving context selection"
            )

        if not recommendations:
            recommendations.append("✅ All metrics within acceptable ranges!")

        return recommendations


def demonstrate_monitoring():
    """모니터링 시스템 시연"""
    print_section("CONTEXT MONITORING DEMO")

    monitor = ContextMonitor(
        cost_threshold_hourly=5.0,
        latency_threshold_ms=2500,
        quality_threshold=0.75,
        token_threshold=8000
    )

    # 시뮬레이션: 다양한 요청 패턴
    print("Simulating production traffic...\n")

    scenarios = [
        # 정상 요청
        {'tokens': 2000, 'latency': 1200, 'quality': 0.85, 'cost': 0.015, 'cached': False, 'model': 'gpt-4-turbo'},
        {'tokens': 1500, 'latency': 800, 'quality': 0.88, 'cost': 0.012, 'cached': False, 'model': 'gpt-4-turbo'},
        {'tokens': 2000, 'latency': 400, 'quality': 0.85, 'cost': 0.0, 'cached': True, 'model': 'gpt-4-turbo'},

        # 고비용 요청
        {'tokens': 15000, 'latency': 3500, 'quality': 0.92, 'cost': 0.12, 'cached': False, 'model': 'gpt-4'},

        # 저품질 요청
        {'tokens': 800, 'latency': 600, 'quality': 0.65, 'cost': 0.003, 'cached': False, 'model': 'gpt-3.5-turbo'},

        # 정상 요청
        {'tokens': 3000, 'latency': 1500, 'quality': 0.82, 'cost': 0.022, 'cached': False, 'model': 'gpt-4-turbo'},
        {'tokens': 2500, 'latency': 900, 'quality': 0.80, 'cost': 0.018, 'cached': False, 'model': 'gpt-4-turbo'},
        {'tokens': 2000, 'latency': 300, 'quality': 0.82, 'cost': 0.0, 'cached': True, 'model': 'gpt-4-turbo'},

        # 고지연 요청
        {'tokens': 7000, 'latency': 4200, 'quality': 0.90, 'cost': 0.05, 'cached': False, 'model': 'gpt-4'},

        # 정상 요청
        {'tokens': 2200, 'latency': 1100, 'quality': 0.84, 'cost': 0.016, 'cached': False, 'model': 'gpt-4-turbo'},
    ]

    base_time = datetime.now() - timedelta(minutes=30)

    for i, scenario in enumerate(scenarios):
        metrics = ContextMetrics(
            timestamp=base_time + timedelta(minutes=i*3),
            query=f"Query {i+1}",
            context_tokens=scenario['tokens'],
            response_tokens=500,
            total_cost=scenario['cost'],
            latency_ms=scenario['latency'],
            quality_score=scenario['quality'],
            cache_hit=scenario['cached'],
            model=scenario['model']
        )

        monitor.log_request(metrics)

    print_success(f"✓ Logged {len(scenarios)} requests\n")

    # 대시보드 표시
    print_section("MONITORING DASHBOARD")

    dashboard = monitor.get_dashboard()

    print(f"{'Metric':<25} {'Value':<20}")
    print("-" * 50)
    print(f"{'Total Requests':<25} {dashboard['total_requests']}")
    print(f"{'Total Cost':<25} ${dashboard['total_cost']:.4f}")
    print(f"{'Avg Latency':<25} {dashboard['avg_latency_ms']:.0f}ms")
    print(f"{'Avg Context Tokens':<25} {dashboard['avg_tokens']:.0f}")

    if dashboard['avg_quality']:
        quality_color = '\033[92m' if dashboard['avg_quality'] >= 0.8 else '\033[93m'
        reset = '\033[0m'
        print(f"{'Avg Quality Score':<25} {quality_color}{dashboard['avg_quality']:.2f}{reset}")

    cache_color = '\033[92m' if dashboard['cache_hit_rate'] >= 0.6 else '\033[91m'
    reset = '\033[0m'
    print(f"{'Cache Hit Rate':<25} {cache_color}{dashboard['cache_hit_rate']*100:.0f}%{reset}")

    # 모델 분포
    print("\nModel Distribution:")
    for model, count in dashboard['model_distribution'].items():
        pct = (count / dashboard['total_requests']) * 100
        print(f"  {model:<20} {count:>3} ({pct:.0f}%)")

    # 알람 표시
    print_section("ALERTS")

    if dashboard['recent_alerts']:
        print(f"Total alerts: {dashboard['alert_count']}\n")
        print(f"{'Level':<12} {'Category':<12} {'Message':<50}")
        print("-" * 80)

        for alert in dashboard['recent_alerts'][:5]:
            level_color = {
                'INFO': '\033[94m',
                'WARNING': '\033[93m',
                'CRITICAL': '\033[91m'
            }[alert.level]
            reset = '\033[0m'

            message = alert.message[:47] + "..." if len(alert.message) > 50 else alert.message
            print(f"{level_color}{alert.level:<12}{reset} {alert.category:<12} {message}")
    else:
        print_success("✓ No alerts")

    # 권장사항
    print_section("RECOMMENDATIONS")

    recommendations = monitor.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"{rec}\n")


def demonstrate_real_time_monitoring():
    """실시간 모니터링 예시"""
    print_section("REAL-TIME MONITORING")

    print("Example monitoring setup:\n")

    print("```python")
    print("from prometheus_client import Counter, Histogram, Gauge")
    print("")
    print("# Metrics")
    print("request_counter = Counter('context_requests_total', 'Total requests')")
    print("cost_counter = Counter('context_cost_total', 'Total cost')")
    print("latency_histogram = Histogram('context_latency_seconds', 'Latency')")
    print("token_gauge = Gauge('context_tokens', 'Context tokens')")
    print("quality_gauge = Gauge('context_quality', 'Quality score')")
    print("")
    print("class MonitoredContextSystem:")
    print("    def __init__(self, monitor: ContextMonitor):")
    print("        self.monitor = monitor")
    print("")
    print("    def process_query(self, query, context):")
    print("        start_time = time.time()")
    print("")
    print("        # Process request")
    print("        response = self.llm.generate(query, context)")
    print("")
    print("        # Record metrics")
    print("        latency = time.time() - start_time")
    print("        metrics = ContextMetrics(")
    print("            timestamp=datetime.now(),")
    print("            query=query,")
    print("            context_tokens=count_tokens(context),")
    print("            response_tokens=count_tokens(response),")
    print("            total_cost=calculate_cost(...),")
    print("            latency_ms=latency * 1000")
    print("        )")
    print("")
    print("        self.monitor.log_request(metrics)")
    print("")
    print("        # Update Prometheus metrics")
    print("        request_counter.inc()")
    print("        cost_counter.inc(metrics.total_cost)")
    print("        latency_histogram.observe(latency)")
    print("        token_gauge.set(metrics.context_tokens)")
    print("")
    print("        return response")
    print("```")


def main():
    demonstrate_monitoring()
    print("\n" + "="*70 + "\n")
    demonstrate_real_time_monitoring()

    print("\n" + "="*70)
    print_section("MONITORING BEST PRACTICES")

    print("1. Metrics to Track:")
    print("   ✓ Cost (per query, hourly, daily)")
    print("   ✓ Latency (p50, p95, p99)")
    print("   ✓ Token usage (context, response)")
    print("   ✓ Quality scores (user feedback, automated)")
    print("   ✓ Cache hit rates")
    print("   ✓ Error rates")

    print("\n2. Alert Thresholds:")
    print("   • Cost: Alert if hourly rate exceeds budget")
    print("   • Latency: p95 > 3s (warning), p99 > 5s (critical)")
    print("   • Quality: Score < 0.7 (warning), < 0.5 (critical)")
    print("   • Cache: Hit rate < 40% (warning)")

    print("\n3. Dashboard Components:")
    print("   • Real-time metrics (last hour)")
    print("   • Trend charts (24h, 7d, 30d)")
    print("   • Cost breakdown by model/query type")
    print("   • Alert history")
    print("   • Optimization recommendations")

    print("\n4. Integration:")
    print("   • Prometheus for metrics collection")
    print("   • Grafana for visualization")
    print("   • PagerDuty/Slack for alerts")
    print("   • CloudWatch/Datadog for logs")

    print("\n5. Review Cadence:")
    print("   • Real-time: Automated alerts")
    print("   • Daily: Cost and quality review")
    print("   • Weekly: Optimization opportunities")
    print("   • Monthly: Strategic planning")

    print("\n💡 Next steps:")
    print("  • Set up monitoring infrastructure")
    print("  • Define alert thresholds")
    print("  • Create monitoring dashboard")
    print("  • Implement automated alerts")
    print("  • Schedule regular reviews")


if __name__ == "__main__":
    main()

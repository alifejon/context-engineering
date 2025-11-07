# Production Patterns

## 개요
프로덕션 환경에서 컨텍스트 엔지니어링을 안정적이고 효율적으로 운영하는 방법을 학습합니다.

## 학습 목표
- 실시간 비용 최적화
- 품질 모니터링 및 알람
- A/B 테스팅을 통한 전략 검증
- 프로덕션 배포 베스트 프랙티스

## 설치

```bash
cd examples/05-production-patterns
pip install -r cost-optimization/requirements.txt
```

## 예제 구조

### 1. Cost Optimization (비용 최적화)
**cost_optimizer.py** - 프로덕션 비용 최적화 시스템
- 스마트 모델 라우팅
- 공격적 캐싱 전략
- 쿼리 복잡도 기반 최적화
- 실시간 비용 추적

**사용법:**
```bash
python cost-optimization/cost_optimizer.py
```

**주요 전략:**
- **스마트 모델 라우팅**: 쿼리 복잡도에 따라 최적 모델 선택
- **캐싱**: 반복 쿼리 80-95% 비용 절감
- **컨텍스트 압축**: 50-70% 토큰 감소
- **배치 처리**: 20-30% 효율 향상

### 2. Context Monitoring (컨텍스트 모니터링)
**context_monitor.py** - 실시간 품질 & 성능 모니터링
- 비용, 지연시간, 품질 추적
- 자동 임계값 알람
- 대시보드 메트릭
- 최적화 권장사항

**사용법:**
```bash
python context-monitoring/context_monitor.py
```

**모니터링 메트릭:**
| 메트릭 | 임계값 | 알람 레벨 |
|--------|--------|-----------|
| 시간당 비용 | $10 | WARNING |
| 지연시간 (p95) | 2.5s | WARNING |
| 품질 점수 | < 0.75 | CRITICAL |
| 컨텍스트 토큰 | > 10K | INFO |
| 캐시 적중률 | < 40% | WARNING |

### 3. A/B Testing (A/B 테스팅)
**ab_tester.py** - 컨텍스트 전략 비교 테스트
- 여러 전략 동시 테스트
- 통계적 유의성 검증
- 효율성 점수 계산
- 자동 승자 선택

**사용법:**
```bash
python ab-testing/ab_tester.py
```

**테스트 가능 항목:**
- 압축률 (30%, 50%, 70%)
- 모델 선택 전략
- 캐시 TTL 설정
- 우선순위화 가중치

## 실행 결과 예시

### Cost Optimization
```
==========================================================
              PRODUCTION COST OPTIMIZATION
==========================================================

Processing 4 queries with different requirements:

Scenario: Simple Factual Query
✓ Selected Model: gpt-3.5-turbo
  Quality Score: 0.75
  Context: 87 → 87 tokens
  Estimated Cost: $0.0013

Scenario: Complex Analysis
✓ Selected Model: gpt-4
  Quality Score: 1.0
  Context: 456 → 273 tokens
  Estimated Cost: $0.0182

Scenario: Cached Query
⚡ Cached! Saved: $0.0013

Total Savings: 62% compared to baseline
```

### Context Monitoring
```
==========================================================
                 MONITORING DASHBOARD
==========================================================

Metric                    Value
--------------------------------------------------
Total Requests            245
Total Cost                $3.2547
Avg Latency               1,245ms
Avg Context Tokens        2,847
Avg Quality Score         0.84
Cache Hit Rate            67%

ALERTS: 3 warnings, 0 critical

RECOMMENDATIONS:
✓ All metrics within acceptable ranges!
```

### A/B Testing
```
==========================================================
                     TEST RESULTS
==========================================================

Strategy                  Samples    Savings    Quality    Efficiency
--------------------------------------------------------------------------
smart_selection          4          68.2%      0.92       0.89
moderate_compression     4          63.1%      0.88       0.85
conservative_compression 4          52.4%      0.95       0.82
aggressive_compression   4          71.5%      0.75       0.78
baseline                 4          0.0%       1.00       0.71

🏆 Winner: smart_selection
  • Cost savings: 68.2%
  • Quality score: 0.92
  • Efficiency: 0.89
```

## 최적화 전략 비교

| 전략 | 절감률 | 구현 난이도 | 유지보수 | 권장 사용 |
|------|--------|-------------|----------|-----------|
| 스마트 라우팅 | 40-60% | 중 | 쉬움 | 모든 경우 |
| 캐싱 | 80-95% | 쉬움 | 중간 | 반복 쿼리 많을 때 |
| 컨텍스트 압축 | 50-70% | 중 | 중간 | 긴 컨텍스트 |
| 배치 처리 | 20-30% | 어려움 | 어려움 | 대량 처리 |
| 토큰 예산 | 30-50% | 쉬움 | 쉬움 | 비용 제한 있을 때 |

## 프로덕션 체크리스트

### 배포 전
- [ ] 비용 임계값 설정
- [ ] 모니터링 대시보드 구축
- [ ] 알람 시스템 연동
- [ ] 폴백 전략 준비
- [ ] 캐시 인프라 구축

### 배포 시
- [ ] 10% 트래픽으로 시작
- [ ] 실시간 메트릭 모니터링
- [ ] 에러율 체크
- [ ] 사용자 피드백 수집
- [ ] 점진적 확대 (50% → 100%)

### 배포 후
- [ ] 일일 비용 리뷰
- [ ] 주간 최적화 회의
- [ ] 월간 전략 평가
- [ ] A/B 테스트 지속 실행
- [ ] 문서 업데이트

## 모니터링 아키텍처

```
┌─────────────┐
│  Application│
│   + Monitor │
└──────┬──────┘
       │
       ├─────→ Prometheus (메트릭 수집)
       │
       ├─────→ CloudWatch/Datadog (로그)
       │
       └─────→ Cache Layer (Redis)

       ↓

┌─────────────────────────────────────┐
│          Grafana Dashboard          │
├─────────────────────────────────────┤
│ • Cost tracking                     │
│ • Latency histograms                │
│ • Quality scores                    │
│ • Model distribution                │
│ • Alert history                     │
└─────────────────────────────────────┘

       ↓

┌─────────────────────────────────────┐
│    Alert Channels                   │
├─────────────────────────────────────┤
│ • Slack notifications               │
│ • PagerDuty (critical)              │
│ • Email digests                     │
└─────────────────────────────────────┘
```

## 비용 최적화 ROI

### 시나리오: 중규모 SaaS
- 월 쿼리: 1M
- 평균 컨텍스트: 5K tokens
- 기본 모델: GPT-4

### Before (최적화 전)
```
월 비용: $150,000
- Input: 5B tokens × $0.03/1K = $150,000
- Output: 500M tokens × $0.06/1K = $30,000
총: $180,000/월
```

### After (최적화 후)
```
스마트 라우팅:      -40% = $72,000 절감
컨텍스트 압축:      -50% 추가 = $36,000 절감
캐싱 (60% 적중):    -54% 추가 = $19,440 절감
────────────────────────────────────────
최종 비용: $52,560/월
절감: $127,440/월 (71%)
연간: $1,529,280 절감
```

## 실전 권장사항

### 1. 초기 설정 (Week 1-2)
```python
# 기본 모니터링
monitor = ContextMonitor(
    cost_threshold_hourly=100.0,  # 시간당 $100 제한
    latency_threshold_ms=2500,     # 2.5초 제한
    quality_threshold=0.75         # 품질 75% 이상
)

# 비용 최적화
optimizer = CostOptimizer()
result = optimizer.optimize_query(query, context, min_quality=0.8)
```

### 2. 안정화 (Week 3-4)
- 임계값 조정
- 캐싱 전략 개선
- 압축률 튜닝
- 알람 노이즈 감소

### 3. 최적화 (Month 2+)
- A/B 테스트 실행
- 새로운 전략 검증
- 모델 업그레이드 평가
- 비용 절감 극대화

## 모범 사례

### ✅ Do
- 실시간 모니터링 구축
- 점진적 최적화 적용
- A/B 테스트로 검증
- 정기적 비용 리뷰
- 사용자 피드백 수집

### ❌ Don't
- 모니터링 없이 배포
- 한번에 여러 변경
- 통계적 검증 생략
- 품질 메트릭 무시
- 폴백 전략 없이 진행

## 다음 단계
- [Context Analyzer Tool](../tools/context-analyzer/) - 컨텍스트 분석 도구
- [Token Optimizer](../tools/token-optimizer/) - 토큰 최적화 유틸
- [Case Studies](../../case-studies/) - 실제 적용 사례

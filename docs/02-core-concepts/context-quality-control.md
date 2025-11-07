# 컨텍스트 품질 관리

## 개요

컨텍스트 품질 관리는 구성된 컨텍스트가 효과적이고 정확한지 지속적으로 모니터링하고 개선하는 프로세스입니다.

## 품질 메트릭

### 1. 관련성 (Relevance)
```python
def measure_relevance(context: str, query: str) -> float:
    """컨텍스트-쿼리 관련성 측정"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([context, query])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return similarity
```

### 2. 완전성 (Completeness)
```python
def measure_completeness(context: str, required_info: list[str]) -> float:
    """필요 정보 포함 여부"""
    context_lower = context.lower()
    found = sum(1 for info in required_info if info.lower() in context_lower)
    return found / len(required_info) if required_info else 0
```

### 3. 간결성 (Conciseness)
```python
def measure_conciseness(context: str, actual_tokens: int, optimal_tokens: int) -> float:
    """토큰 효율성"""
    if actual_tokens <= optimal_tokens:
        return 1.0
    return optimal_tokens / actual_tokens
```

### 4. 일관성 (Consistency)
```python
def check_consistency(context: str) -> dict:
    """컨텍스트 내부 일관성 체크"""
    issues = []

    # 모순 체크 (간단한 예시)
    sentences = context.split('.')
    contradictions = detect_contradictions(sentences)

    # 중복 체크
    duplicates = find_duplicate_info(sentences)

    return {
        "has_contradictions": len(contradictions) > 0,
        "contradictions": contradictions,
        "has_duplicates": len(duplicates) > 0,
        "duplicates": duplicates,
        "consistency_score": 1.0 - (len(contradictions) + len(duplicates)) / len(sentences)
    }
```

## 품질 평가 시스템

```python
class ContextQualityEvaluator:
    """컨텍스트 품질 종합 평가"""

    def evaluate(
        self,
        context: str,
        query: str,
        required_info: list[str] = None,
        optimal_token_count: int = None
    ) -> dict:
        """종합 품질 평가"""

        metrics = {}

        # 1. 관련성
        metrics["relevance"] = measure_relevance(context, query)

        # 2. 완전성
        if required_info:
            metrics["completeness"] = measure_completeness(context, required_info)

        # 3. 간결성
        actual_tokens = count_tokens(context)
        if optimal_token_count:
            metrics["conciseness"] = measure_conciseness(
                context, actual_tokens, optimal_token_count
            )

        # 4. 일관성
        consistency = check_consistency(context)
        metrics["consistency"] = consistency["consistency_score"]

        # 5. 가독성
        metrics["readability"] = self.calculate_readability(context)

        # 종합 점수
        weights = {
            "relevance": 0.3,
            "completeness": 0.25,
            "conciseness": 0.15,
            "consistency": 0.2,
            "readability": 0.1
        }

        total_score = sum(
            metrics.get(k, 0) * weights.get(k, 0)
            for k in weights.keys()
        )

        return {
            "metrics": metrics,
            "total_score": total_score,
            "grade": self.get_grade(total_score),
            "recommendations": self.get_recommendations(metrics)
        }

    def calculate_readability(self, text: str) -> float:
        """가독성 점수"""
        sentences = text.count('.') + text.count('!') + text.count('?')
        words = len(text.split())

        if sentences == 0:
            return 0

        avg_sentence_length = words / sentences

        # 15-20 단어가 이상적
        if 15 <= avg_sentence_length <= 20:
            return 1.0
        elif avg_sentence_length < 15:
            return 0.7 + (avg_sentence_length / 15) * 0.3
        else:
            return max(0, 1.0 - (avg_sentence_length - 20) / 50)

    def get_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 0.9:
            return "A+ Excellent"
        elif score >= 0.8:
            return "A Good"
        elif score >= 0.7:
            return "B Fair"
        elif score >= 0.6:
            return "C Needs Improvement"
        else:
            return "D Poor"

    def get_recommendations(self, metrics: dict) -> list[str]:
        """개선 권장사항"""
        recommendations = []

        if metrics.get("relevance", 1) < 0.7:
            recommendations.append("컨텍스트 관련성이 낮습니다. 쿼리와 더 관련된 내용으로 교체하세요.")

        if metrics.get("completeness", 1) < 0.8:
            recommendations.append("필요한 정보가 누락되었습니다. 추가 컨텍스트를 포함하세요.")

        if metrics.get("conciseness", 1) < 0.7:
            recommendations.append("컨텍스트가 너무 깁니다. 압축을 고려하세요.")

        if metrics.get("consistency", 1) < 0.8:
            recommendations.append("컨텍스트에 모순이나 중복이 있습니다. 정리가 필요합니다.")

        return recommendations
```

## 실시간 품질 모니터링

```python
class ContextQualityMonitor:
    """실시간 품질 모니터링"""

    def __init__(self):
        self.quality_log = []
        self.alerts = []

    def monitor(self, context: str, query: str, response: str) -> dict:
        """컨텍스트 품질 모니터링"""

        evaluator = ContextQualityEvaluator()
        quality = evaluator.evaluate(context, query)

        # 응답 품질도 평가
        response_quality = self.evaluate_response(response, query)

        # 로그 기록
        log_entry = {
            "timestamp": datetime.now(),
            "query": query,
            "context_quality": quality["total_score"],
            "response_quality": response_quality,
            "grade": quality["grade"]
        }
        self.quality_log.append(log_entry)

        # 품질 저하 감지
        if quality["total_score"] < 0.6:
            self.alerts.append({
                "timestamp": datetime.now(),
                "message": "Low context quality detected",
                "score": quality["total_score"],
                "recommendations": quality["recommendations"]
            })

        return {
            "context_quality": quality,
            "response_quality": response_quality,
            "status": "ok" if quality["total_score"] >= 0.7 else "warning"
        }

    def evaluate_response(self, response: str, query: str) -> float:
        """응답 품질 평가 (간단한 휴리스틱)"""
        # 실제로는 더 정교한 평가 필요
        if not response or len(response) < 10:
            return 0.0

        # 쿼리 키워드 포함 여부
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        keyword_overlap = len(query_words & response_words) / len(query_words)

        return keyword_overlap

    def get_quality_trends(self, days: int = 7) -> dict:
        """품질 트렌드 분석"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_logs = [
            log for log in self.quality_log
            if log["timestamp"] >= cutoff
        ]

        if not recent_logs:
            return {}

        avg_quality = sum(log["context_quality"] for log in recent_logs) / len(recent_logs)

        return {
            "period": f"last_{days}_days",
            "average_quality": avg_quality,
            "total_queries": len(recent_logs),
            "alerts_count": len(self.alerts),
            "trend": self.calculate_trend(recent_logs)
        }

    def calculate_trend(self, logs: list) -> str:
        """트렌드 계산"""
        if len(logs) < 2:
            return "insufficient_data"

        first_half = logs[:len(logs)//2]
        second_half = logs[len(logs)//2:]

        avg_first = sum(log["context_quality"] for log in first_half) / len(first_half)
        avg_second = sum(log["context_quality"] for log in second_half) / len(second_half)

        if avg_second > avg_first + 0.05:
            return "improving"
        elif avg_second < avg_first - 0.05:
            return "declining"
        else:
            return "stable"
```

## 자동 품질 개선

```python
class AutoQualityImprover:
    """자동 품질 개선"""

    def improve(self, context: str, query: str, quality_report: dict) -> str:
        """품질 리포트 기반 자동 개선"""

        improved_context = context

        # 관련성 낮음 → 필터링 강화
        if quality_report["metrics"].get("relevance", 1) < 0.7:
            improved_context = self.enhance_relevance(improved_context, query)

        # 간결성 낮음 → 압축
        if quality_report["metrics"].get("conciseness", 1) < 0.7:
            improved_context = self.compress_context(improved_context)

        # 일관성 낮음 → 중복/모순 제거
        if quality_report["metrics"].get("consistency", 1) < 0.8:
            improved_context = self.fix_consistency(improved_context)

        return improved_context

    def enhance_relevance(self, context: str, query: str) -> str:
        """관련성 향상"""
        # 문장 단위로 분리하고 관련성 낮은 것 제거
        sentences = context.split('.')
        relevant_sentences = []

        for sent in sentences:
            if measure_relevance(sent, query) > 0.3:  # 임계값
                relevant_sentences.append(sent)

        return '.'.join(relevant_sentences)

    def compress_context(self, context: str) -> str:
        """컨텍스트 압축"""
        # 추출형 요약 적용
        summarizer = ExtractiveSummarizer(compression_ratio=0.7)
        return summarizer.compress(context)

    def fix_consistency(self, context: str) -> str:
        """일관성 문제 해결"""
        # 중복 문장 제거
        sentences = context.split('.')
        unique_sentences = []
        seen = set()

        for sent in sentences:
            sent = sent.strip()
            if sent and sent not in seen:
                unique_sentences.append(sent)
                seen.add(sent)

        return '. '.join(unique_sentences)
```

## A/B 테스트 프레임워크

```python
class ContextABTesting:
    """컨텍스트 전략 A/B 테스트"""

    def __init__(self):
        self.experiments = {}

    def create_experiment(
        self,
        name: str,
        strategy_a: callable,
        strategy_b: callable
    ):
        """실험 생성"""
        self.experiments[name] = {
            "strategy_a": strategy_a,
            "strategy_b": strategy_b,
            "results_a": [],
            "results_b": []
        }

    def run_test(self, experiment_name: str, query: str, documents: list) -> dict:
        """A/B 테스트 실행"""
        experiment = self.experiments[experiment_name]

        # 랜덤하게 A 또는 B 선택
        import random
        use_a = random.random() < 0.5

        if use_a:
            context = experiment["strategy_a"](query, documents)
            variant = "A"
        else:
            context = experiment["strategy_b"](query, documents)
            variant = "B"

        return {
            "variant": variant,
            "context": context
        }

    def record_result(
        self,
        experiment_name: str,
        variant: str,
        success_score: float
    ):
        """결과 기록"""
        experiment = self.experiments[experiment_name]

        if variant == "A":
            experiment["results_a"].append(success_score)
        else:
            experiment["results_b"].append(success_score)

    def analyze_results(self, experiment_name: str) -> dict:
        """결과 분석"""
        experiment = self.experiments[experiment_name]

        results_a = experiment["results_a"]
        results_b = experiment["results_b"]

        if not results_a or not results_b:
            return {"status": "insufficient_data"}

        avg_a = sum(results_a) / len(results_a)
        avg_b = sum(results_b) / len(results_b)

        # 간단한 통계적 유의성 체크
        improvement = (avg_b - avg_a) / avg_a * 100 if avg_a > 0 else 0

        return {
            "strategy_a_score": avg_a,
            "strategy_b_score": avg_b,
            "improvement": f"{improvement:+.1f}%",
            "winner": "B" if avg_b > avg_a else "A",
            "sample_sizes": {
                "A": len(results_a),
                "B": len(results_b)
            }
        }

# 사용 예시
ab_test = ContextABTesting()

# 실험: 압축 전략 비교
ab_test.create_experiment(
    "compression_strategy",
    strategy_a=lambda q, docs: extractive_compression(q, docs),
    strategy_b=lambda q, docs: hybrid_compression(q, docs)
)

# 테스트 실행
result = ab_test.run_test("compression_strategy", query, documents)

# 사용자 피드백 수집 후 기록
ab_test.record_result("compression_strategy", result["variant"], user_rating)

# 결과 분석
analysis = ab_test.analyze_results("compression_strategy")
print(f"Winner: Strategy {analysis['winner']}")
print(f"Improvement: {analysis['improvement']}")
```

## 요약

**품질 메트릭:**
- 관련성, 완전성, 간결성, 일관성, 가독성

**모니터링:**
- 실시간 품질 추적
- 트렌드 분석
- 자동 알림

**개선:**
- 자동 품질 개선
- A/B 테스트
- 지속적 최적화

**다음**: [고급 패턴](../03-advanced-patterns/) 살펴보기

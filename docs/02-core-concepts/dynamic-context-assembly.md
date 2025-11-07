# 동적 컨텍스트 구성

## 개요

동적 컨텍스트 구성은 쿼리와 상황에 따라 실시간으로 최적의 컨텍스트를 조립하는 기법입니다. 정적인 프롬프트 템플릿을 넘어 지능적으로 컨텍스트를 구성합니다.

## 정적 vs 동적 컨텍스트

### 정적 접근 (Traditional)

```python
# 모든 쿼리에 동일한 컨텍스트 구조
def static_context(query: str) -> str:
    return f"""
System: You are a helpful assistant.

User Profile:
{user_profile}

Knowledge Base:
{all_documents}

Query: {query}
"""
# 문제: 쿼리와 무관한 정보 포함, 비효율적
```

### 동적 접근 (Context Engineering)

```python
# 쿼리에 따라 맞춤형 컨텍스트
def dynamic_context(query: str, context_state: dict) -> str:
    # 1. 쿼리 분석
    query_type = analyze_query(query)

    # 2. 필요한 컨텍스트 결정
    required_contexts = determine_required_contexts(query_type)

    # 3. 각 컨텍스트를 동적으로 검색/생성
    contexts = assemble_contexts(required_contexts, query, context_state)

    # 4. 최적 구조로 조립
    return build_final_context(contexts, query_type)
```

## 동적 구성 컴포넌트

### 1. 쿼리 분석기

```python
class QueryAnalyzer:
    """쿼리 분석 및 분류"""

    def analyze(self, query: str) -> dict:
        """쿼리 특성 분석"""
        return {
            "type": self._classify_type(query),
            "complexity": self._assess_complexity(query),
            "intent": self._extract_intent(query),
            "entities": self._extract_entities(query),
            "requires": self._determine_requirements(query)
        }

    def _classify_type(self, query: str) -> str:
        """쿼리 유형 분류"""
        patterns = {
            "factual": r"\b(what is|define|explain)\b",
            "how_to": r"\b(how to|how do|how can)\b",
            "comparison": r"\b(compare|difference|versus|vs)\b",
            "troubleshooting": r"\b(error|issue|problem|not working)\b",
            "opinion": r"\b(should|recommend|best|better)\b"
        }

        query_lower = query.lower()
        for qtype, pattern in patterns.items():
            if re.search(pattern, query_lower):
                return qtype

        return "general"

    def _assess_complexity(self, query: str) -> str:
        """쿼리 복잡도 평가"""
        # 단어 수, 질문 수, 조건절 등 분석
        words = query.split()
        questions = query.count('?')
        conditionals = len(re.findall(r'\b(if|when|while|unless)\b', query.lower()))

        score = len(words) / 10 + questions * 2 + conditionals

        if score < 3:
            return "simple"
        elif score < 7:
            return "medium"
        else:
            return "complex"

    def _extract_intent(self, query: str) -> list[str]:
        """사용자 의도 추출"""
        intents = []

        if "learn" in query.lower() or "understand" in query.lower():
            intents.append("learning")
        if "buy" in query.lower() or "purchase" in query.lower():
            intents.append("transactional")
        if "find" in query.lower() or "search" in query.lower():
            intents.append("navigational")

        return intents or ["informational"]

    def _extract_entities(self, query: str) -> dict:
        """엔티티 추출 (간단한 구현)"""
        # 실제로는 NER 모델 사용
        entities = {
            "products": [],
            "dates": [],
            "locations": [],
            "technologies": []
        }

        # 간단한 패턴 매칭
        # 실제 구현은 더 정교해야 함
        return entities

    def _determine_requirements(self, query: str) -> list[str]:
        """필요한 컨텍스트 유형 결정"""
        requirements = ["relevant_documents"]  # 기본

        query_lower = query.lower()

        if any(word in query_lower for word in ["recent", "latest", "new"]):
            requirements.append("recent_info")

        if any(word in query_lower for word in ["my", "i", "me"]):
            requirements.append("user_context")

        if "price" in query_lower or "cost" in query_lower:
            requirements.append("pricing_info")

        if "how to" in query_lower or "tutorial" in query_lower:
            requirements.append("instructions")

        return requirements

# 사용 예시
analyzer = QueryAnalyzer()
analysis = analyzer.analyze("How do I optimize my RAG system for cost?")
# {
#     "type": "how_to",
#     "complexity": "medium",
#     "intent": ["learning"],
#     "entities": {"technologies": ["RAG"]},
#     "requires": ["relevant_documents", "instructions"]
# }
```

### 2. 컨텍스트 어셈블러

```python
class ContextAssembler:
    """동적 컨텍스트 어셈블러"""

    def __init__(self):
        self.context_sources = {
            "relevant_documents": self._get_relevant_docs,
            "user_context": self._get_user_context,
            "recent_info": self._get_recent_info,
            "pricing_info": self._get_pricing_info,
            "instructions": self._get_instructions,
            "examples": self._get_examples
        }

    def assemble(
        self,
        query: str,
        query_analysis: dict,
        token_budget: int
    ) -> dict:
        """쿼리에 맞는 컨텍스트 동적 구성"""

        # 필요한 컨텍스트 유형
        required = query_analysis["requires"]

        # 토큰 예산 분배
        budget_allocation = self._allocate_budget(required, token_budget)

        # 각 컨텍스트 수집
        contexts = {}
        for context_type in required:
            if context_type in self.context_sources:
                budget = budget_allocation.get(context_type, 0)
                contexts[context_type] = self.context_sources[context_type](
                    query,
                    query_analysis,
                    budget
                )

        return contexts

    def _allocate_budget(
        self,
        required: list[str],
        total_budget: int
    ) -> dict:
        """토큰 예산을 컨텍스트 유형별로 분배"""

        # 기본 할당 비율
        default_allocations = {
            "relevant_documents": 0.6,
            "user_context": 0.1,
            "recent_info": 0.1,
            "pricing_info": 0.1,
            "instructions": 0.4,
            "examples": 0.3
        }

        # 필요한 것만 추출하고 정규화
        allocations = {k: default_allocations.get(k, 0.1) for k in required}
        total_ratio = sum(allocations.values())

        # 예산 분배
        return {
            k: int(total_budget * (v / total_ratio))
            for k, v in allocations.items()
        }

    def _get_relevant_docs(self, query: str, analysis: dict, budget: int) -> str:
        """관련 문서 검색"""
        # RAG 검색
        docs = vector_search(query, top_k=10)

        # 우선순위화 및 압축
        prioritized = prioritize_documents(docs, query)
        compressed = compress_to_budget(prioritized, budget)

        return compressed

    def _get_user_context(self, query: str, analysis: dict, budget: int) -> str:
        """사용자 컨텍스트"""
        user_profile = get_user_profile()
        user_history = get_user_history(limit=5)

        context = f"User: {user_profile.get('name', 'Unknown')}\n"
        context += f"Preferences: {user_profile.get('preferences', {})}\n"
        context += f"Recent activity: {user_history}"

        return fit_to_budget(context, budget)

    def _get_recent_info(self, query: str, analysis: dict, budget: int) -> str:
        """최신 정보"""
        recent_docs = get_recent_documents(days=7)
        filtered = filter_relevant(recent_docs, query)
        return compress_to_budget(filtered, budget)

    def _get_pricing_info(self, query: str, analysis: dict, budget: int) -> str:
        """가격 정보"""
        pricing_data = get_pricing_data()
        return format_pricing_info(pricing_data, budget)

    def _get_instructions(self, query: str, analysis: dict, budget: int) -> str:
        """사용 방법/튜토리얼"""
        tutorials = search_tutorials(query)
        return compress_to_budget(tutorials, budget)

    def _get_examples(self, query: str, analysis: dict, budget: int) -> str:
        """예제 코드/사례"""
        examples = search_examples(query)
        return compress_to_budget(examples, budget)

# 사용
assembler = ContextAssembler()
contexts = assembler.assemble(
    query="How do I optimize my RAG system?",
    query_analysis=analysis,
    token_budget=4000
)
```

### 3. 컨텍스트 템플릿 엔진

```python
class ContextTemplateEngine:
    """동적 템플릿 엔진"""

    def __init__(self):
        self.templates = {
            "factual": self._factual_template,
            "how_to": self._howto_template,
            "comparison": self._comparison_template,
            "troubleshooting": self._troubleshooting_template
        }

    def build(
        self,
        query_type: str,
        contexts: dict,
        query: str
    ) -> str:
        """쿼리 유형에 맞는 템플릿으로 구성"""
        template_fn = self.templates.get(query_type, self._default_template)
        return template_fn(contexts, query)

    def _factual_template(self, contexts: dict, query: str) -> str:
        """사실 질문용 템플릿"""
        parts = ["# Factual Query Response\n"]

        if "relevant_documents" in contexts:
            parts.append("## Knowledge Base\n")
            parts.append(contexts["relevant_documents"])
            parts.append("\n")

        if "recent_info" in contexts:
            parts.append("## Recent Updates\n")
            parts.append(contexts["recent_info"])
            parts.append("\n")

        parts.append(f"## Query\n{query}\n")
        parts.append("\nProvide a factual, accurate answer based on the above information.")

        return "\n".join(parts)

    def _howto_template(self, contexts: dict, query: str) -> str:
        """How-to 질문용 템플릿"""
        parts = ["# Step-by-Step Guide\n"]

        if "instructions" in contexts:
            parts.append("## Instructions\n")
            parts.append(contexts["instructions"])
            parts.append("\n")

        if "examples" in contexts:
            parts.append("## Examples\n")
            parts.append(contexts["examples"])
            parts.append("\n")

        if "relevant_documents" in contexts:
            parts.append("## Additional Context\n")
            parts.append(contexts["relevant_documents"])
            parts.append("\n")

        parts.append(f"## User Question\n{query}\n")
        parts.append("\nProvide clear, step-by-step instructions.")

        return "\n".join(parts)

    def _comparison_template(self, contexts: dict, query: str) -> str:
        """비교 질문용 템플릿"""
        parts = ["# Comparison Analysis\n"]

        if "relevant_documents" in contexts:
            parts.append("## Reference Information\n")
            parts.append(contexts["relevant_documents"])
            parts.append("\n")

        if "pricing_info" in contexts:
            parts.append("## Pricing Comparison\n")
            parts.append(contexts["pricing_info"])
            parts.append("\n")

        parts.append(f"## Comparison Request\n{query}\n")
        parts.append("\nProvide a structured comparison with pros and cons.")

        return "\n".join(parts)

    def _troubleshooting_template(self, contexts: dict, query: str) -> str:
        """문제 해결용 템플릿"""
        parts = ["# Troubleshooting Guide\n"]

        if "user_context" in contexts:
            parts.append("## User Context\n")
            parts.append(contexts["user_context"])
            parts.append("\n")

        if "relevant_documents" in contexts:
            parts.append("## Known Issues and Solutions\n")
            parts.append(contexts["relevant_documents"])
            parts.append("\n")

        if "examples" in contexts:
            parts.append("## Similar Cases\n")
            parts.append(contexts["examples"])
            parts.append("\n")

        parts.append(f"## Problem Description\n{query}\n")
        parts.append("\nDiagnose the issue and provide solution steps.")

        return "\n".join(parts)

    def _default_template(self, contexts: dict, query: str) -> str:
        """기본 템플릿"""
        parts = []

        for context_type, content in contexts.items():
            parts.append(f"## {context_type.replace('_', ' ').title()}\n")
            parts.append(content)
            parts.append("\n")

        parts.append(f"## Query\n{query}\n")

        return "\n".join(parts)
```

## 완전한 동적 구성 파이프라인

```python
class DynamicContextPipeline:
    """완전한 동적 컨텍스트 구성 파이프라인"""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.analyzer = QueryAnalyzer()
        self.assembler = ContextAssembler()
        self.template_engine = ContextTemplateEngine()

    def build_context(self, query: str, user_state: dict = None) -> dict:
        """쿼리에 최적화된 컨텍스트 동적 생성"""

        # 1. 쿼리 분석
        analysis = self.analyzer.analyze(query)

        # 2. 토큰 예산 계산 (시스템 프롬프트, 출력 버퍼 등 고려)
        available_tokens = self.max_tokens - 500  # 시스템 및 출력용

        # 3. 필요한 컨텍스트 수집
        contexts = self.assembler.assemble(
            query,
            analysis,
            available_tokens
        )

        # 4. 최적 템플릿으로 구성
        final_context = self.template_engine.build(
            analysis["type"],
            contexts,
            query
        )

        # 5. 최종 검증
        actual_tokens = count_tokens(final_context)

        return {
            "context": final_context,
            "analysis": analysis,
            "tokens_used": actual_tokens,
            "tokens_available": self.max_tokens,
            "efficiency": f"{(actual_tokens / self.max_tokens) * 100:.1f}%",
            "contexts_included": list(contexts.keys())
        }

# 사용 예시
pipeline = DynamicContextPipeline(max_tokens=8000)

# 예제 1: How-to 질문
result1 = pipeline.build_context(
    "How do I implement context compression in my RAG system?"
)
print("Query Type:", result1["analysis"]["type"])  # "how_to"
print("Contexts:", result1["contexts_included"])   # ["relevant_documents", "instructions", "examples"]
print("Tokens:", result1["tokens_used"])

# 예제 2: 문제 해결
result2 = pipeline.build_context(
    "My RAG system is returning irrelevant results"
)
print("Query Type:", result2["analysis"]["type"])  # "troubleshooting"
print("Contexts:", result2["contexts_included"])   # ["user_context", "relevant_documents", "examples"]
```

## 적응형 컨텍스트 구성

```python
class AdaptiveContextBuilder:
    """사용자 피드백으로 학습하는 적응형 빌더"""

    def __init__(self):
        self.performance_log = []
        self.optimal_patterns = {}

    def build_and_learn(
        self,
        query: str,
        query_analysis: dict,
        user_feedback: float = None  # 이전 쿼리 피드백
    ) -> dict:
        """구축하고 학습"""

        # 유사한 과거 쿼리 패턴 찾기
        similar_pattern = self._find_similar_pattern(query_analysis)

        if similar_pattern:
            # 성공했던 구성 재사용
            context_config = similar_pattern["config"]
        else:
            # 새로운 구성
            context_config = self._default_config(query_analysis)

        # 컨텍스트 구축
        context = self._build_with_config(query, context_config)

        # 로그 기록
        self._log_usage(query, query_analysis, context_config, user_feedback)

        return {
            "context": context,
            "config_used": context_config,
            "based_on_learning": similar_pattern is not None
        }

    def _find_similar_pattern(self, query_analysis: dict) -> dict:
        """유사한 성공 패턴 찾기"""
        query_type = query_analysis["type"]
        complexity = query_analysis["complexity"]

        # 동일 유형 + 복잡도의 성공 패턴
        key = f"{query_type}_{complexity}"
        return self.optimal_patterns.get(key)

    def _log_usage(
        self,
        query: str,
        analysis: dict,
        config: dict,
        feedback: float
    ):
        """사용 로그"""
        self.performance_log.append({
            "query": query,
            "analysis": analysis,
            "config": config,
            "feedback": feedback,
            "timestamp": datetime.now()
        })

        # 긍정적 피드백 시 최적 패턴 업데이트
        if feedback and feedback > 0.8:
            key = f"{analysis['type']}_{analysis['complexity']}"
            self.optimal_patterns[key] = {
                "config": config,
                "feedback": feedback
            }
```

## 요약

**동적 구성의 핵심 단계:**
1. **분석**: 쿼리 유형, 복잡도, 의도 파악
2. **수집**: 필요한 컨텍스트만 선택적 수집
3. **분배**: 토큰 예산을 동적으로 할당
4. **구성**: 쿼리 유형에 맞는 템플릿 적용
5. **학습**: 피드백으로 지속적 개선

**장점:**
- 쿼리에 최적화된 컨텍스트
- 토큰 효율성 극대화
- 높은 응답 품질
- 비용 절감

**다음**: [컨텍스트 품질 관리](./context-quality-control.md)

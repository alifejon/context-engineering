# 프롬프트 엔지니어링에서 컨텍스트 엔지니어링으로

## 개요
프롬프트 엔지니어링 경험을 Context Engineering으로 확장하는 방법을 배웁니다.

## Prompt Engineering의 한계

### 예제: Few-shot Prompting
```python
# 프롬프트 엔지니어링 방식
prompt = """
Examples:
Q: What is Python?
A: Python is a programming language...

Q: What is JavaScript?
A: JavaScript is a programming language...

[10 more examples...]

Q: What is Rust?
A: """

# 문제점:
# - 예제가 많아지면 토큰 초과
# - 모든 쿼리에 동일한 예제 사용 (비효율적)
# - 예제 선택을 수동으로 해야 함
```

## Context Engineering 접근법

### 동적 Few-shot Selection
```python
class DynamicFewShotSelector:
    """쿼리에 맞는 예제 동적 선택"""

    def __init__(self, example_bank: list):
        self.examples = example_bank
        self.embeddings = self._embed_examples()

    def select_examples(self, query: str, k: int = 3) -> list:
        """쿼리와 유사한 예제 선택"""
        query_embedding = embed_text(query)

        # 유사도 기반 선택
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        top_indices = similarities.argsort()[-k:][::-1]

        return [self.examples[i] for i in top_indices]

    def build_prompt(self, query: str, max_tokens: int = 2000) -> str:
        """동적 프롬프트 구성"""
        # 쿼리에 맞는 예제만 선택
        relevant_examples = self.select_examples(query, k=3)

        # 토큰 예산 내에서 구성
        prompt_parts = ["Answer the following question based on these examples:\n"]

        for ex in relevant_examples:
            example_text = f"Q: {ex['question']}\nA: {ex['answer']}\n\n"
            if count_tokens("\n".join(prompt_parts) + example_text) < max_tokens:
                prompt_parts.append(example_text)

        prompt_parts.append(f"Q: {query}\nA: ")
        return "\n".join(prompt_parts)

# 사용
selector = DynamicFewShotSelector(example_bank)
prompt = selector.build_prompt("What is Rust?", max_tokens=1000)

# 개선:
# ✅ 관련 예제만 사용 (효율적)
# ✅ 토큰 예산 관리
# ✅ 쿼리마다 최적화된 프롬프트
```

## Chain of Thought + Context Engineering

### Before: 정적 CoT
```python
cot_prompt = """
Let's think step by step:
1. First, identify the problem
2. Second, break it down
3. Third, solve each part
4. Finally, combine the solutions

Problem: {problem}
"""
# 모든 문제에 동일한 구조
```

### After: 적응형 CoT
```python
class AdaptiveCoTBuilder:
    """문제 복잡도에 맞는 CoT 구성"""

    def build_cot_prompt(self, problem: str) -> str:
        """문제 분석 후 적절한 CoT 적용"""
        complexity = self._analyze_complexity(problem)

        if complexity == "simple":
            # 간단한 문제: 직접 답변
            return f"Problem: {problem}\nSolution: "

        elif complexity == "medium":
            # 중간: 2-3단계 CoT
            return f"""Let's solve this step by step:
1. Understand: {problem}
2. Solve:
3. Verify:
"""

        else:  # complex
            # 복잡한 문제: 상세 CoT + 예제
            similar_examples = self._find_similar_solved_problems(problem)
            return f"""Here's how to solve similar problems:
{similar_examples}

Now let's solve: {problem}
Step 1: ...
"""

    def _analyze_complexity(self, problem: str) -> str:
        """문제 복잡도 분석"""
        # 단어 수, 조건 수, 수학 연산 등 분석
        word_count = len(problem.split())
        has_conditions = any(word in problem.lower()
                            for word in ["if", "when", "unless"])
        has_math = bool(re.search(r'\d+\s*[\+\-\*/]\s*\d+', problem))

        score = word_count / 10 + has_conditions * 2 + has_math * 2

        if score < 3:
            return "simple"
        elif score < 7:
            return "medium"
        return "complex"

# 토큰 절감:
# - Simple 문제: 50% 토큰 절감
# - Complex 문제: 관련 예제로 정확도 30% 향상
```

## System Prompt Optimization

### Before: 고정 시스템 프롬프트
```python
system_prompt = """
You are a helpful AI assistant.
You should be polite, accurate, and concise.
You should follow these rules:
1. Always verify facts
2. Cite sources when possible
3. Admit when you don't know
... (500 tokens)
"""
# 모든 쿼리에 동일
```

### After: 컨텍스트 인식 시스템 프롬프트
```python
class ContextAwareSystemPrompt:
    """쿼리 유형에 맞는 시스템 프롬프트"""

    def __init__(self):
        self.base = "You are a helpful AI assistant."
        self.role_specific = {
            "code": "You are an expert programmer. Provide clean, efficient code.",
            "math": "You are a math tutor. Explain step by step.",
            "creative": "You are a creative writer. Be imaginative.",
            "factual": "You are a fact-checker. Be precise and cite sources."
        }

    def build(self, query: str, max_tokens: int = 200) -> str:
        """쿼리에 맞는 시스템 프롬프트"""
        query_type = self._classify_query(query)

        prompt = self.base
        if query_type in self.role_specific:
            prompt = self.role_specific[query_type]

        # 토큰 예산 체크
        if count_tokens(prompt) > max_tokens:
            prompt = self.base  # fallback

        return prompt

    def _classify_query(self, query: str) -> str:
        """쿼리 유형 분류"""
        if "code" in query.lower() or "python" in query.lower():
            return "code"
        elif any(word in query.lower() for word in ["calculate", "solve", "equation"]):
            return "math"
        elif any(word in query.lower() for word in ["story", "poem", "creative"]):
            return "creative"
        return "factual"

# 효과:
# - 50-70% 시스템 프롬프트 토큰 절감
# - 쿼리 유형에 최적화된 응답
```

## 핵심 차이점 요약

| 측면 | Prompt Engineering | Context Engineering |
|------|-------------------|---------------------|
| **예제 선택** | 수동, 고정 | 동적, 쿼리 기반 |
| **CoT 적용** | 모든 쿼리 동일 | 복잡도별 적응 |
| **시스템 프롬프트** | 하나로 모든 경우 | 유형별 최적화 |
| **토큰 관리** | 제한 초과 시 에러 | 예산 기반 동적 조정 |
| **최적화 목표** | 프롬프트 품질 | 효율성 + 품질 |

## 실전 전환 가이드

### Step 1: 현재 프롬프트 분석
```python
# 기존 프롬프트 토큰 사용량 측정
current_tokens = count_tokens(your_prompt)
print(f"Current tokens: {current_tokens}")

# 비용 계산
monthly_cost = calculate_monthly_cost(
    avg_tokens=current_tokens,
    queries_per_month=100000,
    model="gpt-4"
)
print(f"Monthly cost: ${monthly_cost}")
```

### Step 2: 동적 구성 적용
```python
# 쿼리 유형별 프롬프트 분리
prompt_templates = {
    "type_a": "template_a with {placeholders}",
    "type_b": "template_b with {placeholders}",
}

def build_prompt(query: str) -> str:
    query_type = classify(query)
    template = prompt_templates[query_type]
    return template.format(query=query)
```

### Step 3: 토큰 예산 설정
```python
# 각 컴포넌트별 토큰 할당
budget = {
    "system": 200,
    "examples": 500,
    "context": 2000,
    "query": 300
}

total = sum(budget.values())  # 3000 tokens
```

### Step 4: 측정 및 최적화
```python
# 개선 효과 측정
new_tokens = count_tokens(optimized_prompt)
improvement = (current_tokens - new_tokens) / current_tokens * 100
print(f"Token reduction: {improvement:.1f}%")
```

## 다음 단계

1. [RAG에 적용하기](./02-enhancing-rag-with-ce.md)
2. [컨텍스트 압축](../docs/02-core-concepts/context-compression.md)
3. [프로덕션 배포](./04-production-deployment.md)

## 요약

**핵심 전환 포인트:**
1. 고정 → 동적
2. 수동 → 자동
3. 전체 → 선택적
4. 품질만 → 효율성 + 품질

Context Engineering은 Prompt Engineering의 진화형입니다!

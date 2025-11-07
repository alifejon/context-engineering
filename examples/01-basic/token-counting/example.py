# Token Counting Example

## 기본 토큰 카운팅

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """정확한 토큰 수 계산"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# 예제
texts = [
    "Hello, world!",
    "Context engineering is important.",
    "안녕하세요, 반갑습니다!"
]

for text in texts:
    tokens = count_tokens(text)
    print(f"Text: {text}")
    print(f"Tokens: {tokens}")
    print(f"Characters: {len(text)}")
    print(f"Ratio: {len(text) / tokens:.2f} chars/token\n")

# Output:
# Text: Hello, world!
# Tokens: 4
# Characters: 13
# Ratio: 3.25 chars/token
#
# Text: Context engineering is important.
# Tokens: 6
# Characters: 34
# Ratio: 5.67 chars/token
#
# Text: 안녕하세요, 반갑습니다!
# Tokens: 13
# Characters: 14
# Ratio: 1.08 chars/token
```

## 토큰 예산 관리

```python
class TokenBudgetManager:
    """토큰 예산 관리"""

    def __init__(self, max_tokens: int, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> int:
        """토큰 수 계산"""
        return len(self.encoding.encode(text))

    def fits_budget(self, text: str) -> bool:
        """예산 내에 맞는지 확인"""
        return self.count(text) <= self.max_tokens

    def truncate_to_budget(self, text: str) -> str:
        """예산에 맞게 자르기"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= self.max_tokens:
            return text

        truncated_tokens = tokens[:self.max_tokens]
        return self.encoding.decode(truncated_tokens)

    def allocate_budget(self, components: dict[str, str]) -> dict[str, str]:
        """여러 컴포넌트에 예산 분배"""
        # 우선순위 순서로 할당
        priority_order = ["system", "query", "context"]

        allocated = {}
        remaining_budget = self.max_tokens

        for component in priority_order:
            if component not in components:
                continue

            text = components[component]
            tokens_needed = self.count(text)

            if tokens_needed <= remaining_budget:
                allocated[component] = text
                remaining_budget -= tokens_needed
            else:
                # 남은 예산으로 자르기
                allocated[component] = self.truncate_to_budget(text)
                break

        return allocated

# 사용 예제
manager = TokenBudgetManager(max_tokens=1000)

components = {
    "system": "You are a helpful assistant.",
    "query": "What is context engineering?",
    "context": "Context engineering is... (long text)"
}

allocated = manager.allocate_budget(components)

for component, text in allocated.items():
    print(f"{component}: {manager.count(text)} tokens")
```

## 실전 사용 예제

```python
def build_prompt_with_budget(
    system_prompt: str,
    user_query: str,
    context_documents: list[str],
    max_total_tokens: int = 8000,
    output_buffer: int = 1000
) -> dict:
    """토큰 예산을 고려한 프롬프트 생성"""

    manager = TokenBudgetManager(max_tokens=max_total_tokens)

    # 필수 컴포넌트 토큰 계산
    system_tokens = manager.count(system_prompt)
    query_tokens = manager.count(user_query)

    # 컨텍스트에 사용 가능한 토큰
    available_for_context = (
        max_total_tokens - system_tokens - query_tokens - output_buffer
    )

    print(f"Token Budget Breakdown:")
    print(f"  Total budget: {max_total_tokens}")
    print(f"  System prompt: {system_tokens}")
    print(f"  User query: {query_tokens}")
    print(f"  Output buffer: {output_buffer}")
    print(f"  Available for context: {available_for_context}")

    # 컨텍스트 문서 선택
    selected_docs = []
    used_tokens = 0

    for doc in context_documents:
        doc_tokens = manager.count(doc)
        if used_tokens + doc_tokens <= available_for_context:
            selected_docs.append(doc)
            used_tokens += doc_tokens
        else:
            break

    final_context = "\n\n".join(selected_docs)

    print(f"  Context used: {used_tokens}")
    print(f"  Documents included: {len(selected_docs)}/{len(context_documents)}")

    return {
        "system": system_prompt,
        "context": final_context,
        "query": user_query,
        "total_tokens": system_tokens + query_tokens + used_tokens,
        "documents_used": len(selected_docs)
    }

# 사용
result = build_prompt_with_budget(
    system_prompt="You are a helpful assistant.",
    user_query="Explain context engineering.",
    context_documents=[doc1, doc2, doc3, doc4, doc5],
    max_total_tokens=8000,
    output_buffer=1000
)

print(f"\nFinal prompt uses {result['total_tokens']} tokens")
```

## 토큰 비용 계산

```python
def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4"
) -> float:
    """토큰 기반 비용 계산"""

    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
    }

    if model not in pricing:
        raise ValueError(f"Unknown model: {model}")

    price = pricing[model]
    cost = (input_tokens * price["input"] + output_tokens * price["output"]) / 1000

    return cost

# 예제
input_tokens = 5000
output_tokens = 500

for model in ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]:
    cost = calculate_cost(input_tokens, output_tokens, model)
    print(f"{model}: ${cost:.4f} per query")

# Output:
# gpt-3.5-turbo: $0.0085 per query
# gpt-4-turbo: $0.0650 per query
# gpt-4: $0.1800 per query

# 월간 비용 (100,000 쿼리 기준)
for model in ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]:
    cost_per_query = calculate_cost(input_tokens, output_tokens, model)
    monthly_cost = cost_per_query * 100000
    print(f"{model}: ${monthly_cost:,.2f} per month")

# Output:
# gpt-3.5-turbo: $850.00 per month
# gpt-4-turbo: $6,500.00 per month
# gpt-4: $18,000.00 per month
```

## 요약

- `tiktoken`으로 정확한 토큰 수 계산
- 토큰 예산 기반 컨텍스트 관리
- 비용 최적화를 위한 모델 선택
- 언어별 토큰 효율성 차이 고려

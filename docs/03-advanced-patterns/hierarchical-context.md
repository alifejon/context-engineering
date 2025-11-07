# 계층적 컨텍스트 구조

## 개요
컨텍스트를 계층적으로 구조화하여 효율적으로 관리합니다.

## 계층 구조

```
Level 1: System Instructions (항상 포함)
Level 2: User Profile (중요도 높음)
Level 3: Conversation History (최근 N턴)
Level 4: Retrieved Knowledge (동적)
Level 5: Examples (필요시)
```

## 구현

```python
class HierarchicalContext:
    """계층적 컨텍스트 관리"""

    def __init__(self, total_budget: int):
        self.budget_allocation = {
            "system": 0.05,      # 5%
            "user": 0.10,        # 10%
            "history": 0.25,     # 25%
            "knowledge": 0.50,   # 50%
            "examples": 0.10     # 10%
        }
        self.total_budget = total_budget

    def build(self, components: dict) -> str:
        """계층별로 컨텍스트 구축"""
        context_parts = []

        for level, ratio in self.budget_allocation.items():
            if level in components:
                budget = int(self.total_budget * ratio)
                content = self.fit_to_budget(components[level], budget)
                context_parts.append(f"# {level.upper()}\n{content}\n")

        return "\n".join(context_parts)

    def fit_to_budget(self, content: str, budget: int) -> str:
        """예산에 맞게 조정"""
        if count_tokens(content) <= budget:
            return content
        return compress_to_budget(content, budget)
```

## 장점
- 명확한 우선순위
- 예측 가능한 토큰 사용
- 모듈식 관리

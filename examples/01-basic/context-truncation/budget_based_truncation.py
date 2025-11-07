#!/usr/bin/env python3
"""
Budget-Based Context Truncation Example

여러 컴포넌트(시스템 프롬프트, 쿼리, 출력)를 고려한
실제 프로덕션 시나리오의 예산 기반 절단 방법입니다.
"""

import sys
import os

# Add parent directory to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    calculate_cost,
    print_section,
    print_success,
    print_warning,
    get_sample_text,
    visualize_comparison
)
from smart_truncation import smart_truncate


class TokenBudgetManager:
    """토큰 예산 관리자"""

    def __init__(self, total_budget: int, model: str = "gpt-4"):
        self.total_budget = total_budget
        self.model = model
        self.allocations = {}

    def allocate(self, components: dict[str, int]) -> dict[str, int]:
        """
        컴포넌트별 토큰 예산 할당

        Args:
            components: 컴포넌트별 비율 또는 고정 토큰 수
                예: {'system': 200, 'output': 1000, 'context': 0}

        Returns:
            컴포넌트별 할당된 토큰 수
        """
        allocated = {}
        remaining = self.total_budget

        # 고정 할당 먼저 처리
        for component, value in components.items():
            if value > 0:
                allocated[component] = value
                remaining -= value
            else:
                allocated[component] = 0

        # 남은 예산을 context에 할당
        if 'context' in components:
            allocated['context'] = max(0, remaining)

        self.allocations = allocated
        return allocated

    def fit_to_budget(self, text: str, budget: int) -> str:
        """텍스트를 예산에 맞게 조정"""
        current_tokens = count_tokens(text, self.model)

        if current_tokens <= budget:
            return text

        # Smart truncation 사용
        return smart_truncate(text, budget, self.model)

    def print_allocation(self):
        """할당 현황 출력"""
        print(f"\n📊 Token Budget Allocation:")
        print(f"{'-'*50}")

        total_allocated = 0
        for component, tokens in self.allocations.items():
            percentage = (tokens / self.total_budget * 100) if self.total_budget > 0 else 0
            print(f"  {component.capitalize():<15} {tokens:>6} tokens ({percentage:>5.1f}%)")
            total_allocated += tokens

        print(f"{'-'*50}")
        print(f"  {'Total':<15} {total_allocated:>6} tokens / {self.total_budget}")

        if total_allocated < self.total_budget:
            unused = self.total_budget - total_allocated
            print(f"  {'Unused':<15} {unused:>6} tokens")
        elif total_allocated > self.total_budget:
            print_warning(f"⚠ Over budget by {total_allocated - self.total_budget} tokens!")


def main():
    print_section("BUDGET-BASED TRUNCATION EXAMPLE")

    # Simulate production scenario
    system_prompt = """You are a helpful AI assistant specialized in technical documentation.
Your responses should be accurate, concise, and well-structured.
Always cite sources when possible and admit when you don't know something."""

    user_query = "Explain how context engineering differs from traditional prompt engineering and provide practical examples."

    context_documents = get_sample_text("large")

    # Component token counts
    system_tokens = count_tokens(system_prompt)
    query_tokens = count_tokens(user_query)
    context_tokens = count_tokens(context_documents)

    print("📋 Input Components:")
    print(f"  System prompt: {format_tokens(system_tokens)}")
    print(f"  User query: {format_tokens(query_tokens)}")
    print(f"  Context documents: {format_tokens(context_tokens)}")
    print(f"  Total before optimization: {format_tokens(system_tokens + query_tokens + context_tokens)}")

    # Set total budget (e.g., GPT-4 with 8K context window)
    total_budget = 8000
    output_buffer = 1500  # Reserve for model output

    print(f"\n🎯 Constraints:")
    print(f"  Total budget: {format_tokens(total_budget)}")
    print(f"  Output buffer: {format_tokens(output_buffer)}")
    print(f"  Available for input: {format_tokens(total_budget - output_buffer)}")

    # Create budget manager
    manager = TokenBudgetManager(total_budget=total_budget - output_buffer)

    # Allocate budget
    allocations = manager.allocate({
        'system': system_tokens,      # Fixed
        'query': query_tokens,         # Fixed
        'context': 0                   # Use remaining budget
    })

    manager.print_allocation()

    # Check if context needs truncation
    available_for_context = allocations['context']

    print(f"\n⚙️ Context Processing:")
    print(f"  Original context: {format_tokens(context_tokens)}")
    print(f"  Available budget: {format_tokens(available_for_context)}")

    if context_tokens > available_for_context:
        print(f"  ⚠ Context exceeds budget by {context_tokens - available_for_context} tokens")
        print(f"\n⏳ Truncating context...")

        optimized_context = manager.fit_to_budget(context_documents, available_for_context)
        optimized_context_tokens = count_tokens(optimized_context)

        print_success(f"Context truncated to {format_tokens(optimized_context_tokens)}")
    else:
        print_success("✓ Context fits within budget!")
        optimized_context = context_documents
        optimized_context_tokens = context_tokens

    # Final totals
    total_after = system_tokens + query_tokens + optimized_context_tokens

    print(f"\n📊 Final Token Usage:")
    print(f"  System: {format_tokens(system_tokens)}")
    print(f"  Query: {format_tokens(query_tokens)}")
    print(f"  Context: {format_tokens(optimized_context_tokens)}")
    print(f"  Input total: {format_tokens(total_after)}")
    print(f"  Output buffer: {format_tokens(output_buffer)}")
    print(f"  Grand total: {format_tokens(total_after + output_buffer)} / {format_tokens(total_budget)}")

    # Cost analysis
    cost_before = calculate_cost(
        system_tokens + query_tokens + context_tokens,
        output_tokens=500,
        model="gpt-4"
    )

    cost_after = calculate_cost(
        total_after,
        output_tokens=500,
        model="gpt-4"
    )

    savings = cost_before - cost_after

    print(f"\n💰 Cost Analysis (GPT-4):")
    print(f"  Before optimization: ${cost_before:.4f} per request")
    print(f"  After optimization: ${cost_after:.4f} per request")
    print(f"  Savings: ${savings:.4f} per request ({(savings/cost_before*100):.1f}%)")

    # Comparison visualization
    visualize_comparison(
        before={
            'total_tokens': system_tokens + query_tokens + context_tokens,
            'context_tokens': context_tokens,
            'cost_per_query': cost_before
        },
        after={
            'total_tokens': total_after,
            'context_tokens': optimized_context_tokens,
            'cost_per_query': cost_after
        }
    )

    # Monthly projections
    print_section("MONTHLY COST PROJECTION")

    queries_per_month = 50000
    monthly_before = cost_before * queries_per_month
    monthly_after = cost_after * queries_per_month
    monthly_savings = monthly_before - monthly_after

    print(f"Assuming {queries_per_month:,} queries per month:")
    print(f"  Before: ${monthly_before:,.2f}/month")
    print(f"  After: ${monthly_after:,.2f}/month")
    print(f"  💰 Savings: ${monthly_savings:,.2f}/month")
    print(f"  Annual savings: ${monthly_savings * 12:,.2f}/year\n")

    # Show optimized prompt structure
    print_section("OPTIMIZED PROMPT STRUCTURE")

    print("System Prompt:")
    print(f"  {system_prompt[:80]}...")
    print(f"  [{system_tokens} tokens]\n")

    print("Context (truncated):")
    print(f"  {optimized_context[:150]}...")
    print(f"  [{optimized_context_tokens} tokens]\n")

    print("User Query:")
    print(f"  {user_query}")
    print(f"  [{query_tokens} tokens]\n")

    print_success("Example complete!")
    print("\n💡 Key Takeaways:")
    print("  1. Always allocate fixed budgets for system/query first")
    print("  2. Use remaining budget for context")
    print("  3. Reserve buffer for model output")
    print("  4. Smart truncation preserves meaning better than simple cutting")


if __name__ == "__main__":
    main()

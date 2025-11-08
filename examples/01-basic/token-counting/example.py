#!/usr/bin/env python3
"""
Token Counting Example

기본 토큰 카운팅과 예산 관리 방법을 시연합니다.
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
    visualize_comparison
)


def basic_counting_example():
    """기본 토큰 카운팅 예제"""
    print_section("BASIC TOKEN COUNTING")

    texts = [
        "Hello, world!",
        "Context engineering is important.",
        "안녕하세요, 반갑습니다!"
    ]

    print(f"{'Text':<40} {'Tokens':<10} {'Chars':<10} {'Ratio':<10}")
    print(f"{'-'*70}")

    for text in texts:
        tokens = count_tokens(text)
        chars = len(text)
        ratio = chars / tokens if tokens > 0 else 0

        print(f"{text:<40} {tokens:<10} {chars:<10} {ratio:<10.2f}")

    print(f"\n💡 Key Observation:")
    print(f"   • English: ~4 chars/token")
    print(f"   • Korean: ~1-2 chars/token (less efficient)")


def budget_example():
    """토큰 예산 관리 예제"""
    print_section("TOKEN BUDGET MANAGEMENT")

    system_prompt = "You are a helpful assistant."
    user_query = "Explain context engineering in detail."
    context = "Context engineering is a systematic approach to managing LLM context windows. " * 50

    system_tokens = count_tokens(system_prompt)
    query_tokens = count_tokens(user_query)
    context_tokens = count_tokens(context)

    print("Components:")
    print(f"  System prompt: {format_tokens(system_tokens)}")
    print(f"  User query: {format_tokens(query_tokens)}")
    print(f"  Context: {format_tokens(context_tokens)}")
    print(f"  Total: {format_tokens(system_tokens + query_tokens + context_tokens)}")

    # Budget management
    max_budget = 4000
    output_buffer = 1000
    available = max_budget - output_buffer - system_tokens - query_tokens

    print(f"\nBudget:")
    print(f"  Max budget: {format_tokens(max_budget)}")
    print(f"  Output buffer: {format_tokens(output_buffer)}")
    print(f"  Available for context: {format_tokens(available)}")

    if context_tokens > available:
        print(f"  ⚠ Context exceeds budget by {context_tokens - available} tokens")
        print(f"  📉 Need to reduce context by {((context_tokens - available) / context_tokens * 100):.1f}%")
    else:
        print(f"  ✓ Context fits within budget")


def cost_analysis():
    """비용 분석 예제"""
    print_section("COST ANALYSIS")

    input_tokens = 3000
    output_tokens = 500

    print(f"Scenario: {format_tokens(input_tokens)} input + {format_tokens(output_tokens)} output")
    print()

    models = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]

    print(f"{'Model':<20} {'Cost/Query':<15} {'Cost/10K Queries':<20}")
    print(f"{'-'*55}")

    for model in models:
        cost = calculate_cost(input_tokens, output_tokens, model)
        cost_10k = cost * 10000

        print(f"{model:<20} ${cost:<14.4f} ${cost_10k:>18,.2f}")

    # Savings calculation
    cheapest = calculate_cost(input_tokens, output_tokens, "gpt-3.5-turbo")
    most_expensive = calculate_cost(input_tokens, output_tokens, "gpt-4")
    savings = most_expensive - cheapest

    print(f"\n💰 Potential Savings:")
    print(f"   Using GPT-3.5 instead of GPT-4: ${savings:.4f} per query")
    print(f"   Monthly (100K queries): ${savings * 100000:,.2f}")


def main():
    basic_counting_example()
    budget_example()
    cost_analysis()

    print_success("\nExample complete!")
    print("\n💡 Next steps:")
    print("  • Try multi_model_counting.py for model comparisons")
    print("  • Try cost_calculator.py for interactive calculations")


if __name__ == "__main__":
    main()

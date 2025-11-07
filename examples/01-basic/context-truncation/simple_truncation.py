#!/usr/bin/env python3
"""
Simple Context Truncation Example

가장 기본적인 토큰 기반 절단 방법입니다.
토큰 수가 제한을 초과하면 뒤에서부터 자릅니다.
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
import tiktoken


def simple_truncate(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Simply truncate text to max_tokens.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        model: Model name for tokenization

    Returns:
        Truncated text
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Truncate to max_tokens
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)

    return truncated_text


def main():
    print_section("SIMPLE TRUNCATION EXAMPLE")

    # Get sample text
    original_text = get_sample_text("large")
    original_tokens = count_tokens(original_text)

    print(f"Original text: {format_tokens(original_tokens)}")
    print(f"\nFirst 200 characters:")
    print(f"{original_text[:200]}...\n")

    # Set target token limit
    max_tokens = 1000

    print(f"Target limit: {format_tokens(max_tokens)}")

    # Perform simple truncation
    print("\n⏳ Truncating...")
    truncated_text = simple_truncate(original_text, max_tokens)
    truncated_tokens = count_tokens(truncated_text)

    print_success(f"Truncation complete!")

    # Show results
    print(f"\n📊 Results:")
    print(f"  Original: {format_tokens(original_tokens)}")
    print(f"  Truncated: {format_tokens(truncated_tokens)}")
    print(f"  Reduction: {((original_tokens - truncated_tokens) / original_tokens * 100):.1f}%")

    # Calculate cost savings
    cost_before = calculate_cost(original_tokens, model="gpt-4")
    cost_after = calculate_cost(truncated_tokens, model="gpt-4")
    savings = cost_before - cost_after

    print(f"\n💰 Cost Analysis (GPT-4):")
    print(f"  Before: ${cost_before:.4f} per request")
    print(f"  After: ${cost_after:.4f} per request")
    print(f"  Savings: ${savings:.4f} per request ({(savings/cost_before*100):.1f}%)")

    # Show truncated text preview
    print(f"\n📄 Truncated Text Preview:")
    print(f"{'-'*60}")
    print(truncated_text[:300])
    if len(truncated_text) > 300:
        print(f"... [+{len(truncated_text)-300} more characters]")
    print(f"{'-'*60}")

    # Check if text ends cleanly
    if not truncated_text.rstrip().endswith(('.', '!', '?', '\n')):
        print_warning("Text may be cut mid-sentence!")
        print(f"Last 50 characters: ...{truncated_text[-50:]}")

    # Comparison visualization
    visualize_comparison(
        before={'tokens': original_tokens, 'cost_per_query': cost_before},
        after={'tokens': truncated_tokens, 'cost_per_query': cost_after}
    )

    print_section("MONTHLY COST PROJECTION")

    queries_per_month = 100000
    monthly_before = cost_before * queries_per_month
    monthly_after = cost_after * queries_per_month
    monthly_savings = monthly_before - monthly_after

    print(f"Assuming {queries_per_month:,} queries per month:")
    print(f"  Before: ${monthly_before:,.2f}/month")
    print(f"  After: ${monthly_after:,.2f}/month")
    print(f"  💰 Savings: ${monthly_savings:,.2f}/month\n")

    print_success("Example complete!")
    print("\n💡 Tip: Use smart_truncation.py for better quality (sentence-aware)")


if __name__ == "__main__":
    main()

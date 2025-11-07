#!/usr/bin/env python3
"""
Smart Context Truncation Example

문장 경계를 고려한 지능적 절단 방법입니다.
의미를 보존하면서 자연스러운 지점에서 자릅니다.
"""

import sys
import os
import re

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


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Simple sentence splitting (can be improved with NLTK)
    sentences = re.split(r'([.!?]\s+)', text)

    # Recombine sentences with their punctuation
    result = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            result.append(sentences[i] + sentences[i+1])
        else:
            result.append(sentences[i])

    if len(sentences) % 2 == 1:
        result.append(sentences[-1])

    return [s.strip() for s in result if s.strip()]


def smart_truncate(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text at sentence boundaries.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        model: Model name for tokenization

    Returns:
        Truncated text that ends at a sentence boundary
    """
    # Split into sentences
    sentences = split_sentences(text)

    if not sentences:
        return text

    # Build truncated text sentence by sentence
    truncated = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence, model)

        if current_tokens + sentence_tokens <= max_tokens:
            truncated.append(sentence)
            current_tokens += sentence_tokens
        else:
            break

    # If no sentences fit, fall back to simple truncation
    if not truncated:
        encoding = __import__('tiktoken').encoding_for_model(model)
        tokens = encoding.encode(text)
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)

    return ' '.join(truncated)


def main():
    print_section("SMART TRUNCATION EXAMPLE")

    # Get sample text
    original_text = get_sample_text("large")
    original_tokens = count_tokens(original_text)

    print(f"Original text: {format_tokens(original_tokens)}")

    # Count sentences
    sentences = split_sentences(original_text)
    print(f"Sentences: {len(sentences)}")
    print(f"\nFirst sentence:")
    print(f"  {sentences[0]}\n")

    # Set target token limit
    max_tokens = 1000

    print(f"Target limit: {format_tokens(max_tokens)}")

    # Perform smart truncation
    print("\n⏳ Truncating (sentence-aware)...")
    truncated_text = smart_truncate(original_text, max_tokens)
    truncated_tokens = count_tokens(truncated_text)

    print_success("Truncation complete!")

    # Show results
    print(f"\n📊 Results:")
    print(f"  Original: {format_tokens(original_tokens)}")
    print(f"  Truncated: {format_tokens(truncated_tokens)}")
    print(f"  Reduction: {((original_tokens - truncated_tokens) / original_tokens * 100):.1f}%")

    # Count sentences in truncated text
    truncated_sentences = split_sentences(truncated_text)
    print(f"  Sentences kept: {len(truncated_sentences)}/{len(sentences)}")

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
    print(truncated_text[:400])
    if len(truncated_text) > 400:
        print(f"\n... [+{len(truncated_text)-400} more characters]\n")

    # Show last sentence
    print(f"Last sentence:")
    print(f"  {truncated_sentences[-1]}")
    print(f"{'-'*60}")

    # Check text quality
    if truncated_text.rstrip().endswith(('.', '!', '?')):
        print_success("✓ Text ends cleanly at sentence boundary")
    else:
        print_warning("⚠ Text may not end at sentence boundary")

    # Comparison with simple truncation
    print_section("COMPARISON: SMART vs SIMPLE")

    from simple_truncation import simple_truncate
    simple_truncated = simple_truncate(original_text, max_tokens)
    simple_tokens = count_tokens(simple_truncated)

    print(f"Smart Truncation:")
    print(f"  Tokens: {format_tokens(truncated_tokens)}")
    print(f"  Ends cleanly: {'Yes' if truncated_text.rstrip().endswith(('.', '!', '?')) else 'No'}")

    print(f"\nSimple Truncation:")
    print(f"  Tokens: {format_tokens(simple_tokens)}")
    print(f"  Ends cleanly: {'Yes' if simple_truncated.rstrip().endswith(('.', '!', '?')) else 'No'}")

    token_diff = abs(truncated_tokens - simple_tokens)
    print(f"\nToken difference: {token_diff} tokens")
    print(f"Quality trade-off: Worth it for better readability!\n")

    # Comparison visualization
    visualize_comparison(
        before={'tokens': original_tokens, 'sentences': len(sentences), 'cost_per_query': cost_before},
        after={'tokens': truncated_tokens, 'sentences': len(truncated_sentences), 'cost_per_query': cost_after}
    )

    print_success("Example complete!")
    print("\n💡 Tip: Use budget_based_truncation.py for production scenarios")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Multi-Model Token Counting

여러 LLM 모델의 토큰화 방식을 비교하고
모델 선택에 도움을 제공합니다.
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
    get_sample_text
)


def compare_models(text: str) -> dict:
    """
    여러 모델의 토큰 수 비교

    Args:
        text: 분석할 텍스트

    Returns:
        모델별 토큰 수 및 비용 정보
    """
    models = {
        "gpt-4": {"encoding": "cl100k_base", "input_price": 0.03, "output_price": 0.06},
        "gpt-4-turbo": {"encoding": "cl100k_base", "input_price": 0.01, "output_price": 0.03},
        "gpt-3.5-turbo": {"encoding": "cl100k_base", "input_price": 0.0015, "output_price": 0.002},
    }

    results = {}

    for model_name, model_info in models.items():
        token_count = count_tokens(text, model_name)
        cost_per_query = calculate_cost(token_count, output_tokens=500, model=model_name)

        results[model_name] = {
            "tokens": token_count,
            "cost_per_query": cost_per_query,
            "input_price_per_1k": model_info["input_price"],
            "output_price_per_1k": model_info["output_price"]
        }

    return results


def analyze_language_efficiency(texts: dict) -> dict:
    """
    언어별 토큰 효율성 분석

    Args:
        texts: 언어별 텍스트 샘플

    Returns:
        언어별 토큰 효율성
    """
    results = {}

    for lang, text in texts.items():
        tokens = count_tokens(text, "gpt-4")
        chars = len(text)
        words = len(text.split())

        results[lang] = {
            "characters": chars,
            "words": words,
            "tokens": tokens,
            "chars_per_token": chars / tokens if tokens > 0 else 0,
            "tokens_per_word": tokens / words if words > 0 else 0
        }

    return results


def main():
    print_section("MULTI-MODEL TOKEN COUNTING")

    # Get sample text
    text = get_sample_text("medium")

    print(f"Sample Text ({len(text)} characters):")
    print(f"{'-'*60}")
    print(f"{text[:200]}...")
    print(f"{'-'*60}\n")

    # Compare models
    print("⏳ Analyzing across models...\n")

    results = compare_models(text)

    # Display comparison table
    print_section("MODEL COMPARISON")

    print(f"{'Model':<20} {'Tokens':<12} {'Cost/Query':<15} {'Cost/1M queries':<15}")
    print(f"{'-'*75}")

    for model_name, data in results.items():
        tokens = data["tokens"]
        cost_per_query = data["cost_per_query"]
        cost_per_million = cost_per_query * 1_000_000

        print(f"{model_name:<20} {tokens:<12} ${cost_per_query:<14.4f} ${cost_per_million:>13,.0f}")

    # Find best options
    print(f"\n{'─'*75}")
    cheapest = min(results.items(), key=lambda x: x[1]["cost_per_query"])
    print(f"💰 Most cost-effective: {cheapest[0]} (${cheapest[1]['cost_per_query']:.4f}/query)")

    # Token count comparison
    token_counts = [data["tokens"] for data in results.values()]
    if max(token_counts) == min(token_counts):
        print(f"📊 Token counts: Identical across all models ({token_counts[0]} tokens)")
    else:
        print(f"📊 Token count range: {min(token_counts)} - {max(token_counts)} tokens")

    # Language efficiency analysis
    print_section("LANGUAGE EFFICIENCY ANALYSIS")

    language_samples = {
        "English": "Hello, world! This is a test of token efficiency.",
        "Korean": "안녕하세요! 토큰 효율성 테스트입니다.",
        "Spanish": "¡Hola, mundo! Esta es una prueba de eficiencia.",
        "Chinese": "你好世界！这是一个令牌效率测试。",
        "Code": "def hello():\n    print('Hello, world!')\n    return True"
    }

    lang_results = analyze_language_efficiency(language_samples)

    print(f"{'Language':<12} {'Chars':<8} {'Words':<8} {'Tokens':<8} {'Chars/Token':<12}")
    print(f"{'-'*60}")

    for lang, data in lang_results.items():
        print(f"{lang:<12} {data['characters']:<8} {data['words']:<8} {data['tokens']:<8} {data['chars_per_token']:<12.2f}")

    # Insights
    print_section("KEY INSIGHTS")

    print("1. Model Selection:")
    print("   • GPT-3.5: Best for cost-sensitive applications (20x cheaper than GPT-4)")
    print("   • GPT-4: Best for quality-critical tasks")
    print("   • GPT-4-Turbo: Balanced option (3x cheaper than GPT-4)")

    print("\n2. Language Efficiency:")
    best_lang = max(lang_results.items(), key=lambda x: x[1]['chars_per_token'])
    worst_lang = min(lang_results.items(), key=lambda x: x[1]['chars_per_token'])

    print(f"   • Most efficient: {best_lang[0]} ({best_lang[1]['chars_per_token']:.1f} chars/token)")
    print(f"   • Least efficient: {worst_lang[0]} ({worst_lang[1]['chars_per_token']:.1f} chars/token)")
    print(f"   • Efficiency ratio: {best_lang[1]['chars_per_token'] / worst_lang[1]['chars_per_token']:.1f}x")

    print("\n3. Cost Optimization:")
    gpt4_cost = results["gpt-4"]["cost_per_query"]
    gpt35_cost = results["gpt-3.5-turbo"]["cost_per_query"]
    savings = gpt4_cost - gpt35_cost

    print(f"   • Switching from GPT-4 to GPT-3.5 saves ${savings:.4f} per query")
    print(f"   • For 100K queries/month: ${savings * 100000:,.0f} savings")

    # Practical recommendations
    print_section("RECOMMENDATIONS")

    print("Use GPT-3.5-turbo when:")
    print("  ✓ Cost is primary concern")
    print("  ✓ Task is straightforward")
    print("  ✓ High query volume")

    print("\nUse GPT-4 when:")
    print("  ✓ Quality is critical")
    print("  ✓ Complex reasoning needed")
    print("  ✓ Lower query volume")

    print("\nUse GPT-4-turbo when:")
    print("  ✓ Need balance of cost and quality")
    print("  ✓ Long context windows needed")
    print("  ✓ Production deployment")

    # ROI calculation
    print_section("ROI EXAMPLE")

    print("Scenario: Customer support chatbot")
    print("  • 50,000 queries/month")
    print("  • Average input: 2,000 tokens")
    print("  • Average output: 500 tokens")

    for model in ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]:
        cost = calculate_cost(2000, 500, model)
        monthly = cost * 50000
        print(f"\n  {model}:")
        print(f"    Cost per query: ${cost:.4f}")
        print(f"    Monthly cost: ${monthly:,.2f}")


if __name__ == "__main__":
    main()

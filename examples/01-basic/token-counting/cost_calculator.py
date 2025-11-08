#!/usr/bin/env python3
"""
Interactive Cost Calculator

실시간으로 LLM 비용을 계산하고
다양한 시나리오를 비교하는 도구입니다.
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
    print_success
)


class CostCalculator:
    """LLM 비용 계산기"""

    def __init__(self):
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06, "context": 8000},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03, "context": 128000},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002, "context": 16000},
            "claude-3-opus": {"input": 0.015, "output": 0.075, "context": 200000},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015, "context": 200000},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125, "context": 200000},
        }

    def calculate_query_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> dict:
        """단일 쿼리 비용 계산"""
        if model not in self.pricing:
            raise ValueError(f"Unknown model: {model}")

        prices = self.pricing[model]
        input_cost = (input_tokens * prices["input"]) / 1000
        output_cost = (output_tokens * prices["output"]) / 1000
        total_cost = input_cost + output_cost

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    def calculate_monthly_cost(
        self,
        model: str,
        queries_per_month: int,
        avg_input_tokens: int,
        avg_output_tokens: int
    ) -> dict:
        """월간 비용 계산"""
        query_cost = self.calculate_query_cost(
            model, avg_input_tokens, avg_output_tokens
        )

        monthly_cost = query_cost["total_cost"] * queries_per_month

        return {
            "queries_per_month": queries_per_month,
            "cost_per_query": query_cost["total_cost"],
            "monthly_cost": monthly_cost,
            "annual_cost": monthly_cost * 12,
            "breakdown": query_cost
        }

    def compare_models(
        self,
        queries_per_month: int,
        avg_input_tokens: int,
        avg_output_tokens: int
    ) -> dict:
        """여러 모델 비용 비교"""
        results = {}

        for model in self.pricing.keys():
            results[model] = self.calculate_monthly_cost(
                model, queries_per_month, avg_input_tokens, avg_output_tokens
            )

        return results

    def calculate_roi(
        self,
        current_model: str,
        new_model: str,
        queries_per_month: int,
        avg_input_tokens: int,
        avg_output_tokens: int,
        implementation_cost: float = 0
    ) -> dict:
        """ROI 계산"""
        current = self.calculate_monthly_cost(
            current_model, queries_per_month, avg_input_tokens, avg_output_tokens
        )
        new = self.calculate_monthly_cost(
            new_model, queries_per_month, avg_input_tokens, avg_output_tokens
        )

        monthly_savings = current["monthly_cost"] - new["monthly_cost"]
        annual_savings = monthly_savings * 12

        if monthly_savings <= 0:
            break_even_months = float('inf')
        else:
            break_even_months = implementation_cost / monthly_savings if monthly_savings > 0 else 0

        return {
            "current_model": current_model,
            "new_model": new_model,
            "current_monthly_cost": current["monthly_cost"],
            "new_monthly_cost": new["monthly_cost"],
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "implementation_cost": implementation_cost,
            "break_even_months": break_even_months,
            "roi_1_year": ((annual_savings - implementation_cost) / implementation_cost * 100) if implementation_cost > 0 else float('inf')
        }


def interactive_calculator():
    """인터랙티브 계산기 모드"""
    print_section("INTERACTIVE COST CALCULATOR")

    calc = CostCalculator()

    print("Available models:")
    for i, model in enumerate(calc.pricing.keys(), 1):
        ctx = calc.pricing[model]["context"]
        print(f"  {i}. {model} (context: {ctx:,} tokens)")

    # Get user input
    print("\nEnter your scenario:")

    model = input("Model (default: gpt-4-turbo): ").strip() or "gpt-4-turbo"
    if model not in calc.pricing:
        print(f"Unknown model, using gpt-4-turbo")
        model = "gpt-4-turbo"

    try:
        queries = int(input("Queries per month (default: 10000): ") or "10000")
        input_tokens = int(input("Average input tokens (default: 2000): ") or "2000")
        output_tokens = int(input("Average output tokens (default: 500): ") or "500")
    except ValueError:
        print("Invalid input, using defaults")
        queries = 10000
        input_tokens = 2000
        output_tokens = 500

    # Calculate
    print("\n⏳ Calculating...")

    result = calc.calculate_monthly_cost(
        model, queries, input_tokens, output_tokens
    )

    # Display results
    print_section("COST ANALYSIS")

    print(f"Model: {model}")
    print(f"Queries: {queries:,} per month")
    print(f"Average tokens: {input_tokens:,} input + {output_tokens:,} output")

    print(f"\nPer Query:")
    print(f"  Input cost:  ${result['breakdown']['input_cost']:.6f}")
    print(f"  Output cost: ${result['breakdown']['output_cost']:.6f}")
    print(f"  Total:       ${result['cost_per_query']:.6f}")

    print(f"\nMonthly:")
    print(f"  Total cost:  ${result['monthly_cost']:,.2f}")

    print(f"\nAnnual:")
    print(f"  Total cost:  ${result['annual_cost']:,.2f}")

    # Comparison
    print_section("COMPARISON WITH OTHER MODELS")

    comparisons = calc.compare_models(queries, input_tokens, output_tokens)

    print(f"{'Model':<20} {'Monthly':<15} {'Annual':<15} {'vs Current':<15}")
    print(f"{'-'*70}")

    for comp_model, comp_result in sorted(comparisons.items(), key=lambda x: x[1]['monthly_cost']):
        monthly = comp_result['monthly_cost']
        annual = comp_result['annual_cost']
        diff = monthly - result['monthly_cost']

        if comp_model == model:
            marker = "→"
        else:
            marker = " "

        print(f"{marker} {comp_model:<18} ${monthly:>12,.2f}  ${annual:>12,.2f}  {diff:>+13,.2f}")

    # Savings opportunity
    cheapest = min(comparisons.items(), key=lambda x: x[1]['monthly_cost'])
    if cheapest[0] != model:
        savings = result['monthly_cost'] - cheapest[1]['monthly_cost']
        print(f"\n💰 Potential savings with {cheapest[0]}: ${savings:,.2f}/month (${savings*12:,.2f}/year)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LLM Cost Calculator")
    parser.add_argument("--model", default="gpt-4-turbo", help="Model name")
    parser.add_argument("--queries", type=int, default=10000, help="Queries per month")
    parser.add_argument("--input-tokens", type=int, default=2000, help="Average input tokens")
    parser.add_argument("--output-tokens", type=int, default=500, help="Average output tokens")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--compare", action="store_true", help="Compare all models")

    args = parser.parse_args()

    calc = CostCalculator()

    if args.interactive:
        interactive_calculator()
        return

    if args.compare:
        # Compare all models
        print_section("MODEL COST COMPARISON")

        print(f"Scenario:")
        print(f"  Queries: {args.queries:,} per month")
        print(f"  Average: {args.input_tokens:,} input + {args.output_tokens:,} output tokens\n")

        results = calc.compare_models(args.queries, args.input_tokens, args.output_tokens)

        print(f"{'Model':<20} {'Per Query':<15} {'Monthly':<15} {'Annual':<15}")
        print(f"{'-'*70}")

        for model, result in sorted(results.items(), key=lambda x: x[1]['monthly_cost']):
            per_query = result['cost_per_query']
            monthly = result['monthly_cost']
            annual = result['annual_cost']

            print(f"{model:<20} ${per_query:<14.6f} ${monthly:>13,.2f}  ${annual:>13,.2f}")

        # Best options
        print(f"\n{'─'*70}")
        cheapest = min(results.items(), key=lambda x: x[1]['monthly_cost'])
        print(f"💰 Most cost-effective: {cheapest[0]} (${cheapest[1]['monthly_cost']:,.2f}/month)")

        return

    # Single model calculation
    result = calc.calculate_monthly_cost(
        args.model, args.queries, args.input_tokens, args.output_tokens
    )

    print_section(f"COST ANALYSIS: {args.model.upper()}")

    print(f"Configuration:")
    print(f"  Queries: {args.queries:,} per month")
    print(f"  Tokens: {args.input_tokens:,} input + {args.output_tokens:,} output")

    print(f"\nCosts:")
    print(f"  Per query: ${result['cost_per_query']:.6f}")
    print(f"  Monthly:   ${result['monthly_cost']:,.2f}")
    print(f"  Annual:    ${result['annual_cost']:,.2f}")

    print_success("\nCalculation complete!")
    print("\n💡 Tip: Use --compare to see all models or --interactive for custom scenarios")


if __name__ == "__main__":
    main()

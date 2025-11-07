"""Common utilities for all examples."""

import os
import tiktoken
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text for a specific model.

    Args:
        text: Text to count tokens for
        model: Model name (gpt-4, gpt-3.5-turbo, etc.)

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Default to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def load_api_key(service: str = "openai") -> Optional[str]:
    """
    Load API key from environment variables.

    Args:
        service: Service name (openai, anthropic, cohere)

    Returns:
        API key or None if not found
    """
    key_names = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "cohere": "COHERE_API_KEY"
    }

    key_name = key_names.get(service.lower())
    if not key_name:
        return None

    return os.getenv(key_name)


def log_metrics(metrics: Dict[str, Any], title: str = "Metrics"):
    """
    Log metrics in a formatted way.

    Args:
        metrics: Dictionary of metrics
        title: Title for the metrics section
    """
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^50}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}\n")

    for key, value in metrics.items():
        formatted_key = key.replace('_', ' ').title()
        if isinstance(value, float):
            if 0 < value < 1:
                print(f"{formatted_key:.<40} {value:.2%}")
            else:
                print(f"{formatted_key:.<40} {value:.2f}")
        elif isinstance(value, int):
            print(f"{formatted_key:.<40} {value:,}")
        else:
            print(f"{formatted_key:.<40} {value}")

    print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}\n")


def visualize_comparison(before: Dict[str, Any], after: Dict[str, Any]):
    """
    Visualize before/after comparison.

    Args:
        before: Before metrics
        after: After metrics
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'BEFORE vs AFTER COMPARISON':^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    print(f"{'Metric':<20} {'Before':>15} {'After':>15} {'Change':>10}")
    print(f"{'-'*60}")

    for key in before.keys():
        if key in after:
            before_val = before[key]
            after_val = after[key]

            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    change = ((after_val - before_val) / before_val) * 100
                    change_str = f"{change:+.1f}%"

                    # Color code the change
                    if change < 0:
                        color = Colors.GREEN  # Reduction is good for tokens/cost
                    elif change > 0:
                        color = Colors.RED
                    else:
                        color = Colors.YELLOW
                else:
                    change_str = "N/A"
                    color = Colors.YELLOW

                # Format values
                if isinstance(before_val, float):
                    before_str = f"{before_val:.2f}"
                    after_str = f"{after_val:.2f}"
                else:
                    before_str = f"{before_val:,}"
                    after_str = f"{after_val:,}"

                formatted_key = key.replace('_', ' ').title()
                print(f"{formatted_key:<20} {before_str:>15} {after_str:>15} {color}{change_str:>10}{Colors.ENDC}")

    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def format_tokens(tokens: int) -> str:
    """
    Format token count with thousand separators.

    Args:
        tokens: Number of tokens

    Returns:
        Formatted string
    """
    return f"{tokens:,} tokens"


def calculate_cost(input_tokens: int, output_tokens: int = 0, model: str = "gpt-4") -> float:
    """
    Calculate cost for token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name

    Returns:
        Cost in dollars
    """
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    }

    if model not in pricing:
        model = "gpt-4"  # Default

    price = pricing[model]
    cost = (input_tokens * price["input"] + output_tokens * price["output"]) / 1000

    return cost


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def get_sample_text(size: str = "medium") -> str:
    """
    Get sample text for testing.

    Args:
        size: small, medium, or large

    Returns:
        Sample text
    """
    texts = {
        "small": """
Context engineering is a systematic approach to managing LLM context windows.
It involves techniques like compression, prioritization, and dynamic assembly.
The goal is to maximize efficiency while maintaining quality.
""",
        "medium": """
Context engineering is a systematic approach to managing LLM context windows.
It encompasses various advanced techniques including intelligent compression algorithms,
strategic prioritization frameworks, and dynamic context assembly mechanisms.

The field has emerged as a critical discipline in production LLM systems, where
cost optimization and performance are paramount concerns. Unlike traditional
prompt engineering which focuses on what to ask, context engineering focuses
on how to efficiently manage the information provided to the LLM.

Key techniques include:
1. Context Compression - Reducing token count while preserving information
2. Context Prioritization - Selecting most relevant information
3. Dynamic Assembly - Building context based on query type
4. Quality Control - Monitoring and improving context quality

These approaches can reduce costs by 60-80% while improving response quality
by 10-15%. The investment in context engineering typically pays for itself
within 3-6 months for production systems processing thousands of queries daily.
""",
        "large": """
Context engineering is a systematic approach to managing LLM context windows.
It encompasses various advanced techniques including intelligent compression algorithms,
strategic prioritization frameworks, and dynamic context assembly mechanisms.
These approaches are designed to maximize the efficient utilization of limited
context window resources while maintaining high quality outputs.

The field has emerged as a critical discipline in production LLM systems, where
cost optimization and performance are paramount concerns. As organizations deploy
LLM-powered applications at scale, the costs associated with token usage can
quickly escalate into tens or hundreds of thousands of dollars per month.

Historical Context:
The evolution of context engineering can be traced through three major phases.
First came prompt engineering (2020-2021), which focused on crafting effective
prompts and instructions. Then RAG (Retrieval-Augmented Generation) emerged
in 2021-2023, adding the capability to incorporate external knowledge. Finally,
context engineering (2023-present) addresses the challenge of efficiently
managing all the information that goes into the LLM.

Core Principles:
1. Efficiency - Use only necessary information, eliminate redundancy
2. Relevance - Prioritize information most relevant to the query
3. Adaptability - Dynamically adjust based on context and requirements

Key Techniques:
1. Context Compression - Multiple approaches exist:
   - Extractive: Select important sentences using TF-IDF or embeddings
   - Abstractive: Use LLMs to summarize and rephrase
   - Semantic: Remove duplicate information while preserving meaning
   - Hybrid: Combine multiple approaches for optimal results

2. Context Prioritization - Rank information by:
   - Relevance: Similarity to query
   - Recency: Time-based decay functions
   - Credibility: Source trustworthiness
   - Specificity: Concrete vs abstract information

3. Dynamic Assembly - Build context based on:
   - Query type (factual, how-to, comparison, troubleshooting)
   - Query complexity (simple, medium, complex)
   - User context (history, preferences, role)
   - Available budget (token limits, cost constraints)

4. Quality Control - Monitor and improve:
   - Relevance scores
   - Information completeness
   - Token efficiency
   - Response quality

Business Impact:
Organizations implementing context engineering have reported:
- 60-80% reduction in token costs
- 40-50% improvement in response times
- 10-15% increase in accuracy
- Better user satisfaction scores

The ROI is typically positive within 3-6 months for systems processing
thousands of queries daily. For a system handling 100,000 queries per month,
the cost savings alone can exceed $100,000 annually.

Implementation Considerations:
Success requires attention to:
- Accurate token counting and budget management
- Quality metrics and monitoring
- A/B testing of different strategies
- Continuous optimization based on feedback
- Balance between automation and human oversight

Future Directions:
The field continues to evolve with research into:
- Learned compression models
- Multi-modal context management
- Context caching strategies
- Personalized context optimization
- Real-time adaptive systems
"""
    }

    return texts.get(size, texts["medium"]).strip()

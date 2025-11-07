#!/usr/bin/env python3
"""
Query-Aware Context Building

쿼리 유형을 분석하여 맞춤형 컨텍스트를 구성합니다.
"""

import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    print_section,
    print_success,
    get_sample_text
)


class QueryAnalyzer:
    """쿼리 분석기"""

    def analyze(self, query: str) -> dict:
        """
        쿼리 분석

        Args:
            query: 사용자 쿼리

        Returns:
            분석 결과
        """
        return {
            'type': self._classify_type(query),
            'complexity': self._assess_complexity(query),
            'intent': self._extract_intent(query),
            'keywords': self._extract_keywords(query),
            'requires': self._determine_requirements(query)
        }

    def _classify_type(self, query: str) -> str:
        """쿼리 유형 분류"""
        patterns = {
            'factual': r'\b(what is|define|explain|describe)\b',
            'how_to': r'\b(how to|how do|how can|how should)\b',
            'comparison': r'\b(compare|difference|versus|vs|better)\b',
            'troubleshooting': r'\b(error|issue|problem|fix|debug)\b',
            'opinion': r'\b(should|recommend|best|suggest)\b'
        }

        query_lower = query.lower()
        for qtype, pattern in patterns.items():
            if re.search(pattern, query_lower):
                return qtype

        return 'general'

    def _assess_complexity(self, query: str) -> str:
        """쿼리 복잡도 평가"""
        words = query.split()
        questions = query.count('?')
        conditionals = len(re.findall(r'\b(if|when|while|unless)\b', query.lower()))

        score = len(words) / 10 + questions * 2 + conditionals

        if score < 3:
            return 'simple'
        elif score < 7:
            return 'medium'
        else:
            return 'complex'

    def _extract_intent(self, query: str) -> list[str]:
        """사용자 의도 추출"""
        intents = []

        query_lower = query.lower()

        if any(word in query_lower for word in ['learn', 'understand', 'know']):
            intents.append('learning')
        if any(word in query_lower for word in ['buy', 'purchase', 'price']):
            intents.append('transactional')
        if any(word in query_lower for word in ['find', 'search', 'locate']):
            intents.append('navigational')

        return intents or ['informational']

    def _extract_keywords(self, query: str) -> list[str]:
        """키워드 추출"""
        # 간단한 구현: 불용어 제거 후 단어 추출
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords[:5]  # 상위 5개

    def _determine_requirements(self, query: str) -> list[str]:
        """필요한 컨텍스트 유형 결정"""
        requirements = ['relevant_documents']  # 기본

        query_lower = query.lower()

        if any(word in query_lower for word in ['recent', 'latest', 'new']):
            requirements.append('recent_info')

        if any(word in query_lower for word in ['example', 'sample', 'demo']):
            requirements.append('examples')

        if any(word in query_lower for word in ['how to', 'tutorial', 'guide']):
            requirements.append('instructions')

        return requirements


class ContextBuilder:
    """쿼리 인식 컨텍스트 빌더"""

    def __init__(self):
        self.analyzer = QueryAnalyzer()

    def build_context(self, query: str, available_docs: list[str], max_tokens: int) -> dict:
        """
        쿼리에 맞는 컨텍스트 구성

        Args:
            query: 사용자 쿼리
            available_docs: 사용 가능한 문서들
            max_tokens: 최대 토큰 수

        Returns:
            구성된 컨텍스트 정보
        """
        # 쿼리 분석
        analysis = self.analyzer.analyze(query)

        # 쿼리 유형에 따른 템플릿 선택
        template = self._select_template(analysis['type'])

        # 토큰 예산 분배
        budget = self._allocate_budget(analysis, max_tokens)

        # 관련 문서 선택
        selected_docs = self._select_documents(
            available_docs,
            query,
            budget['documents']
        )

        # 최종 컨텍스트 구성
        final_context = self._assemble_context(
            template,
            query,
            selected_docs,
            analysis
        )

        return {
            'analysis': analysis,
            'template': template,
            'budget': budget,
            'selected_docs': len(selected_docs),
            'context': final_context,
            'tokens': count_tokens(final_context)
        }

    def _select_template(self, query_type: str) -> str:
        """쿼리 유형에 맞는 템플릿 선택"""
        templates = {
            'factual': 'factual_qa',
            'how_to': 'tutorial',
            'comparison': 'comparison',
            'troubleshooting': 'problem_solving',
            'opinion': 'recommendation',
            'general': 'general_qa'
        }
        return templates.get(query_type, 'general_qa')

    def _allocate_budget(self, analysis: dict, max_tokens: int) -> dict:
        """토큰 예산 분배"""
        # 복잡도에 따라 예산 조정
        if analysis['complexity'] == 'simple':
            doc_ratio = 0.6
        elif analysis['complexity'] == 'medium':
            doc_ratio = 0.7
        else:
            doc_ratio = 0.8

        return {
            'instructions': int(max_tokens * 0.1),
            'documents': int(max_tokens * doc_ratio),
            'examples': int(max_tokens * (1 - doc_ratio - 0.1))
        }

    def _select_documents(self, docs: list[str], query: str, budget: int) -> list[str]:
        """문서 선택"""
        # 간단한 관련성 기반 선택
        selected = []
        total_tokens = 0

        for doc in docs:
            tokens = count_tokens(doc)
            if total_tokens + tokens <= budget:
                selected.append(doc)
                total_tokens += tokens
            else:
                break

        return selected

    def _assemble_context(
        self,
        template: str,
        query: str,
        docs: list[str],
        analysis: dict
    ) -> str:
        """최종 컨텍스트 조립"""
        parts = []

        # 템플릿별 구조
        if template == 'tutorial':
            parts.append("# Step-by-Step Guide\n")
            parts.append("## Context\n")
            parts.append("\n\n".join(docs))
            parts.append(f"\n\n## Question\n{query}")
            parts.append("\n\nProvide clear, step-by-step instructions.")

        elif template == 'comparison':
            parts.append("# Comparison Analysis\n")
            parts.append("## Reference Information\n")
            parts.append("\n\n".join(docs))
            parts.append(f"\n\n## Comparison Request\n{query}")
            parts.append("\n\nProvide a structured comparison.")

        else:  # general_qa, factual
            parts.append("# Question Answering\n")
            parts.append("## Knowledge Base\n")
            parts.append("\n\n".join(docs))
            parts.append(f"\n\n## Query\n{query}")

        return "\n".join(parts)


def demonstrate_query_aware_context():
    """쿼리 인식 컨텍스트 빌더 시연"""
    print_section("QUERY-AWARE CONTEXT BUILDING")

    # 다양한 쿼리 유형
    queries = [
        "What is context engineering?",
        "How do I implement context compression in my RAG system?",
        "Compare extractive and abstractive summarization methods.",
        "My RAG system is returning irrelevant results, how do I fix it?",
        "What's the best compression strategy for production?"
    ]

    # 샘플 문서
    available_docs = [
        get_sample_text("medium"),
        "Context compression reduces tokens while preserving information.",
        "Extractive summarization selects important sentences from the original text.",
        "Abstractive summarization generates new text that captures the essence.",
        "RAG systems can be improved through better retrieval and reranking.",
    ]

    builder = ContextBuilder()

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Example {i}")
        print(f"{'='*60}")

        print(f"\nQuery: {query}")

        # 컨텍스트 구성
        result = builder.build_context(query, available_docs, max_tokens=2000)

        # 분석 결과
        analysis = result['analysis']
        print(f"\n📊 Query Analysis:")
        print(f"  Type: {analysis['type']}")
        print(f"  Complexity: {analysis['complexity']}")
        print(f"  Intent: {', '.join(analysis['intent'])}")
        print(f"  Keywords: {', '.join(analysis['keywords'])}")

        # 템플릿 및 예산
        print(f"\n🎯 Context Strategy:")
        print(f"  Template: {result['template']}")
        print(f"  Token budget:")
        for component, tokens in result['budget'].items():
            print(f"    {component}: {format_tokens(tokens)}")

        # 최종 컨텍스트
        print(f"\n📄 Generated Context:")
        print(f"  Selected documents: {result['selected_docs']}")
        print(f"  Total tokens: {format_tokens(result['tokens'])}")
        print(f"  Preview:")
        preview = result['context'][:200].replace('\n', ' ')
        print(f"    {preview}...")

    print_section("KEY INSIGHTS")

    print("쿼리 유형별 전략:")
    print("\n1. Factual (정의/설명):")
    print("   • 간결한 컨텍스트")
    print("   • 신뢰할 수 있는 출처 우선")

    print("\n2. How-to (방법/튜토리얼):")
    print("   • 단계별 구조")
    print("   • 예제 포함")
    print("   • 더 많은 토큰 할당")

    print("\n3. Comparison (비교):")
    print("   • 구조화된 형식")
    print("   • 양측 정보 균형")

    print("\n4. Troubleshooting (문제 해결):")
    print("   • 사용자 컨텍스트 포함")
    print("   • 유사 사례 참조")

    print_success("\nQuery-aware context building complete!")


def main():
    demonstrate_query_aware_context()

    print("\n💡 Benefits:")
    print("  • Each query gets optimized context")
    print("  • Better token utilization")
    print("  • Improved response quality")
    print("  • Consistent structure")


if __name__ == "__main__":
    main()

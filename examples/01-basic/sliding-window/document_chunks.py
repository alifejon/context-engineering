#!/usr/bin/env python3
"""
Document Chunking Example

긴 문서를 슬라이딩 윈도우로 청크화하여
순차적으로 처리하는 방법을 시연합니다.
"""

import sys
import os
from typing import List, Tuple

# Add parent directory to path for shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.utils import (
    count_tokens,
    format_tokens,
    print_section,
    print_success,
    get_sample_text
)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100,
    model: str = "gpt-4"
) -> List[Tuple[str, int, int]]:
    """
    텍스트를 오버랩이 있는 청크로 분할

    Args:
        text: 분할할 텍스트
        chunk_size: 청크당 최대 토큰 수
        overlap: 청크 간 오버랩 토큰 수
        model: 토큰화 모델

    Returns:
        (청크 텍스트, 시작 위치, 끝 위치) 튜플 리스트
    """
    import tiktoken

    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        # 청크 끝 위치 계산
        end = min(start + chunk_size, len(tokens))

        # 청크 디코딩
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)

        chunks.append((chunk_text, start, end))

        # 다음 청크 시작 위치 (오버랩 고려)
        if end >= len(tokens):
            break

        start = end - overlap

    return chunks


def main():
    print_section("DOCUMENT CHUNKING WITH SLIDING WINDOW")

    # 긴 문서 로드
    document = get_sample_text("large")
    total_tokens = count_tokens(document)

    print(f"Document Information:")
    print(f"  Total length: {len(document):,} characters")
    print(f"  Total tokens: {format_tokens(total_tokens)}")
    print(f"  First 100 chars: {document[:100]}...\n")

    # 청킹 파라미터
    chunk_size = 1000
    overlap = 200

    print(f"Chunking Parameters:")
    print(f"  Chunk size: {format_tokens(chunk_size)}")
    print(f"  Overlap: {format_tokens(overlap)}")
    print(f"  Overlap ratio: {(overlap/chunk_size*100):.1f}%\n")

    # 청킹 수행
    print("⏳ Chunking document...")
    chunks = chunk_text(document, chunk_size=chunk_size, overlap=overlap)

    print_success(f"Created {len(chunks)} chunks!\n")

    # 청크 정보 출력
    print_section("CHUNK ANALYSIS")

    total_chunk_tokens = 0
    for i, (chunk, start, end) in enumerate(chunks, 1):
        chunk_tokens = end - start
        total_chunk_tokens += chunk_tokens

        print(f"Chunk {i}:")
        print(f"  Token range: [{start:,} - {end:,}]")
        print(f"  Tokens: {format_tokens(chunk_tokens)}")
        print(f"  Characters: {len(chunk):,}")

        # Preview
        preview = chunk[:100].replace('\n', ' ')
        print(f"  Preview: {preview}...")

        # 오버랩 확인
        if i > 1:
            prev_end = chunks[i-2][2]
            overlap_tokens = prev_end - start
            if overlap_tokens > 0:
                print(f"  Overlap with previous: {format_tokens(overlap_tokens)}")

        print()

    # 통계
    print_section("STATISTICS")

    redundancy = (total_chunk_tokens - total_tokens) / total_tokens * 100

    print(f"Original document: {format_tokens(total_tokens)}")
    print(f"Total chunk tokens: {format_tokens(total_chunk_tokens)}")
    print(f"Redundancy due to overlap: {redundancy:.1f}%")

    avg_chunk_size = total_chunk_tokens / len(chunks)
    print(f"Average chunk size: {format_tokens(int(avg_chunk_size))}")

    # 처리 시나리오
    print_section("PROCESSING SCENARIO")

    print("Example use case: Analyzing a long document")
    print("\nSequential Processing:")

    for i, (chunk, start, end) in enumerate(chunks, 1):
        chunk_tokens = end - start
        print(f"\n  Step {i}: Process chunk {i}")
        print(f"    Tokens: {format_tokens(chunk_tokens)}")
        print(f"    Action: Send to LLM for analysis")
        print(f"    Output: Extract key points, entities, etc.")

    # 비용 계산
    from shared.utils import calculate_cost

    # 방법 1: 전체 문서를 한 번에 (불가능하거나 비효율적)
    cost_full = calculate_cost(total_tokens, output_tokens=500, model="gpt-4")

    # 방법 2: 청크별 처리
    cost_chunks = sum(
        calculate_cost(end - start, output_tokens=100, model="gpt-4")
        for _, start, end in chunks
    )

    print_section("COST COMPARISON")

    print(f"Full document (if possible):")
    print(f"  Input: {format_tokens(total_tokens)}")
    print(f"  Cost: ${cost_full:.4f}")

    print(f"\nChunked processing:")
    print(f"  Total input: {format_tokens(total_chunk_tokens)} (with overlap)")
    print(f"  Cost: ${cost_chunks:.4f}")

    print(f"\nDifference: ${abs(cost_chunks - cost_full):.4f}")

    if cost_chunks > cost_full:
        print("  ⚠ Chunked processing costs more due to overlap")
        print("  💡 But it enables processing documents larger than context window!")
    else:
        print("  ✓ Chunked processing is more economical")

    print_section("OPTIMIZATION TIPS")

    print("1. Overlap Size:")
    print("   • Too small: May lose context between chunks")
    print("   • Too large: Wastes tokens and increases cost")
    print("   • Recommended: 10-20% of chunk size")

    print("\n2. Chunk Size:")
    print("   • Smaller chunks: More API calls, more overlap cost")
    print("   • Larger chunks: Fewer calls, better context")
    print("   • Balance based on your use case")

    print("\n3. Processing Strategy:")
    print("   • Sequential: Process chunks one by one")
    print("   • Parallel: Process independent chunks simultaneously")
    print("   • Hierarchical: Summarize chunks, then combine")

    print_success("\nExample complete!")


if __name__ == "__main__":
    main()

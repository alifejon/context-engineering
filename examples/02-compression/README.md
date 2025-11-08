# Context Compression Examples

## 개요
컨텍스트를 압축하여 토큰 수를 줄이면서 핵심 정보를 보존하는 다양한 기법을 학습합니다.

## 학습 목표
- 추출형, 생성형, 의미적 압축 이해
- 압축률과 품질의 트레이드오프
- 실전에서 사용 가능한 압축 전략

## 설치

```bash
cd examples/02-compression
pip install -r summarization-based/requirements.txt
```

## 예제 구조

### 1. Summarization-Based (요약 기반)
**extractive_summary.py** - TF-IDF 기반 추출형 요약
- 원문에서 중요한 문장 선택
- 빠르고 정확
- 30-50% 압축률

**사용법:**
```bash
python summarization-based/extractive_summary.py
```

### 2. Semantic Compression (의미적 압축)
**deduplicate.py** - 의미적 중복 제거
- 유사한 내용 병합
- RAG 결과 최적화
- 30-40% 중복 제거

**사용법:**
```bash
python semantic-compression/deduplicate.py
```

### 3. Hybrid Compression (하이브리드)
**README.md** - 여러 기법 조합
- 2단계 압축 (의미적 → 추출형)
- 최고의 품질/효율 균형

## 압축 방법 비교

| 방법 | 압축률 | 속도 | 품질 | 비용 | 사용 사례 |
|------|--------|------|------|------|----------|
| 추출형 | 30-50% | 빠름 | 높음 | 무료 | 대부분의 경우 |
| 의미적 | 30-40% | 중간 | 높음 | 무료 | RAG 중복 제거 |
| 하이브리드 | 50-70% | 중간 | 높음 | 무료 | 프로덕션 권장 |

## 실행 결과 예시

```
==========================================================
                EXTRACTIVE SUMMARIZATION
==========================================================

Original: 2,456 tokens
Compressed (50%): 1,228 tokens
Compressed (30%): 737 tokens

💰 Cost Savings (30% compression):
  Before: $0.0736/query
  After: $0.0221/query
  Savings: $0.0515/query (70%)

Monthly (100K queries): $5,150 savings
```

## 실전 권장사항

### 1. 단계별 접근
```python
# Step 1: 의미적 중복 제거
deduped = deduplicate(documents)

# Step 2: 추출형 압축
compressed = extractive_summarize(deduped, ratio=0.3)
```

### 2. 압축률 선택
- **50%**: 안전한 시작점
- **30%**: 균형잡힌 선택 (권장)
- **20%**: 공격적 압축

### 3. 품질 확인
- 핵심 키워드 보존 확인
- 문장 완결성 체크
- A/B 테스트로 검증

## 다음 단계
- [Prioritization](../03-prioritization/) - 우선순위 기반 선택
- [Dynamic Assembly](../04-dynamic-assembly/) - 동적 컨텍스트 구성

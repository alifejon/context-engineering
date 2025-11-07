# Context Prioritization Examples

## 개요
제한된 토큰 예산 내에서 가장 중요한 정보를 선택하는 우선순위화 기법을 학습합니다.

## 학습 목표
- 관련성, 최신성, 중요도 기반 점수화
- 복합 점수 시스템 구축
- 토큰 예산 내 최적 선택

## 설치

```bash
cd examples/03-prioritization
pip install -r relevance-scoring/requirements.txt
```

## 예제 구조

### 1. Relevance Scoring (관련성 점수화)
**tfidf_scoring.py** - TF-IDF 기반 관련성 평가
- 쿼리와의 유사도 계산
- 상위 K개 선택
- 토큰 예산 기반 선택

**사용법:**
```bash
python relevance-scoring/tfidf_scoring.py
```

**주요 기능:**
- 문서별 관련성 점수
- Top-K 선택
- 예산 기반 자동 선택

## 우선순위화 기준

### 1. 관련성 (Relevance)
```python
score = cosine_similarity(doc, query)
```
- 쿼리와의 의미적 유사도
- 가장 기본적인 기준
- 가중치: 40-50%

### 2. 최신성 (Recency)
```python
score = exp(-age_days / decay_period)
```
- 시간 기반 감쇠
- 뉴스, 이벤트에 중요
- 가중치: 20-30%

### 3. 신뢰도 (Credibility)
```python
score = source_trust_level
```
- 출처 기반 평가
- 공식 문서 우선
- 가중치: 10-20%

### 4. 구체성 (Specificity)
```python
score = (numbers + examples) / length
```
- 구체적 정보 우선
- 예제, 수치 포함
- 가중치: 10-20%

## 실행 결과 예시

```
==========================================================
                RELEVANCE SCORES
==========================================================

Rank   Score      Tokens     Preview
----------------------------------------------------------------------
1      0.856      124        Context engineering is a systematic...
       ████████████████
2      0.742      98         Token economics focuses on...
       ██████████████
3      0.621      156        Context compression reduces...
       ████████████

Top 3 Average Score: 0.740 ✓ Good relevance!
```

## 복합 점수 시스템

```python
final_score = (
    relevance * 0.4 +
    recency * 0.2 +
    credibility * 0.2 +
    specificity * 0.2
)
```

### 쿼리 유형별 가중치 조정

| 쿼리 유형 | 관련성 | 최신성 | 신뢰도 | 구체성 |
|----------|--------|--------|--------|--------|
| Factual | 30% | 10% | 40% | 20% |
| News | 40% | 40% | 10% | 10% |
| How-to | 40% | 10% | 20% | 30% |

## 실전 워크플로우

```python
# 1. 검색 (넉넉하게)
docs = vector_search(query, k=20)

# 2. 점수화
scored = score_documents(docs, query)

# 3. 선택 (예산 내)
selected = select_top_k(scored, max_tokens=4000)

# 4. 검증
if avg_score(selected) < 0.3:
    # 쿼리 개선 또는 더 검색
```

## 성능 지표

### 좋은 우선순위화
- ✓ 평균 점수 > 0.3
- ✓ 상위 5개로 충분
- ✓ 토큰 예산 90% 이상 활용

### 개선 필요
- ✗ 평균 점수 < 0.2
- ✗ 상위 10개도 부족
- ✗ 토큰 예산 50% 미만 사용

## 다음 단계
- [Compression](../02-compression/) - 압축과 함께 사용
- [Dynamic Assembly](../04-dynamic-assembly/) - 동적 구성에 통합

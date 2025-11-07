# Token Counting Examples

## 개요
정확한 토큰 계산과 비용 분석 방법을 배웁니다.

## 학습 목표
- tiktoken을 사용한 정확한 토큰 카운팅
- 모델별 토큰화 차이 이해
- 비용 계산 및 최적화

## 설치

```bash
cd examples/01-basic/token-counting
pip install -r requirements.txt
```

## 예제

### 1. Basic Example (example.py)
기본적인 토큰 카운팅과 예산 관리

```bash
python example.py
```

**특징:**
- tiktoken을 사용한 정확한 카운팅
- 토큰 예산 관리
- 비용 계산

### 2. Multi-Model Counting (multi_model_counting.py)
여러 모델의 토큰화 비교

```bash
python multi_model_counting.py
```

**특징:**
- GPT-4, GPT-3.5, Claude 등 비교
- 모델별 토큰 효율성
- 언어별 차이 분석

### 3. Cost Calculator (cost_calculator.py)
실시간 비용 계산기

```bash
python cost_calculator.py
```

**특징:**
- 인터랙티브 비용 계산
- 월간 비용 추정
- ROI 분석

### 4. Batch Analysis (batch_analysis.py)
대량 텍스트 분석

```bash
python batch_analysis.py --input documents/
```

**특징:**
- 여러 파일 일괄 분석
- CSV/JSON 출력
- 통계 리포트

## 주요 개념

### 토큰이란?
- LLM이 처리하는 텍스트의 기본 단위
- 단어, 단어의 일부, 또는 문자일 수 있음
- 모델마다 토큰화 방식이 다름

### 토큰 효율성
- 영어: 평균 1 token ≈ 4 characters
- 한글: 평균 1 token ≈ 1.5-2 characters
- 코드: 평균 1 token ≈ 3-4 characters

## 예상 출력

```
==========================================================
                TOKEN COUNTING ANALYSIS
==========================================================

Text: "Context engineering is essential..."

Model Comparison:
  GPT-4:          156 tokens
  GPT-3.5:        156 tokens
  Claude 3:       158 tokens

Cost Comparison (per 1M tokens):
  GPT-4:          $30.00 input
  GPT-3.5:        $1.50 input
  Claude 3:       $3.00 input

Best for cost: GPT-3.5
Best for quality: GPT-4
```

## 실전 팁

1. **항상 정확한 토큰 수 계산**
   ```python
   import tiktoken
   enc = tiktoken.encoding_for_model("gpt-4")
   tokens = len(enc.encode(text))
   ```

2. **예산 계획 수립**
   ```python
   budget = max_tokens - system_tokens - output_buffer
   context = fit_to_budget(documents, budget)
   ```

3. **비용 모니터링**
   ```python
   cost = (input_tokens * price_input + output_tokens * price_output) / 1000
   log_cost(cost)
   ```

## 다음 단계
- [Context Truncation](../context-truncation/) - 토큰 제한 처리
- [Token Economics](../../../docs/01-fundamentals/token-economics.md) - 비용 최적화

# Context Truncation Examples

## 개요
컨텍스트가 토큰 제한을 초과할 때 효과적으로 절단하는 방법을 배웁니다.

## 학습 목표
- 토큰 제한 처리 방법 이해
- 정보 손실 최소화 전략
- 문장/단락 경계를 고려한 스마트 절단

## 설치

```bash
cd examples/01-basic/context-truncation
pip install -r requirements.txt
```

## 예제

### 1. Simple Truncation (simple_truncation.py)
가장 기본적인 토큰 기반 절단

```bash
python simple_truncation.py
```

**특징:**
- 토큰 단위로 정확하게 절단
- 빠르고 간단함
- 문장 중간에서 잘릴 수 있음

### 2. Smart Truncation (smart_truncation.py)
문장 경계를 고려한 지능적 절단

```bash
python smart_truncation.py
```

**특징:**
- 문장 경계에서 절단
- 의미 보존
- 약간의 추가 처리 시간

### 3. Budget-Based Truncation (budget_based_truncation.py)
여러 컴포넌트를 고려한 예산 기반 절단

```bash
python budget_based_truncation.py
```

**특징:**
- 시스템 프롬프트, 쿼리, 출력 버퍼 고려
- 실제 프로덕션 시나리오
- 우선순위 기반 할당

## 비교

| 방법 | 속도 | 품질 | 사용 사례 |
|------|------|------|----------|
| Simple | 매우 빠름 | 낮음 | 프로토타입, 테스트 |
| Smart | 빠름 | 높음 | 대부분의 경우 |
| Budget-Based | 중간 | 매우 높음 | 프로덕션 |

## 예상 출력

```
==========================================================
                    SIMPLE TRUNCATION
==========================================================

Original text: 2,456 tokens
Target: 1,000 tokens

[절단된 텍스트 표시]

Final: 1,000 tokens (59.3% reduction)
Cost savings: $0.087 per request

⚠ Warning: Text may be cut mid-sentence
```

## 다음 단계
- [Sliding Window](../sliding-window/) - 멀티턴 대화 관리
- [Token Counting](../token-counting/) - 정확한 토큰 계산
- [Context Compression](../../02-compression/) - 고급 압축 기법

# Sliding Window Examples

## 개요
멀티턴 대화에서 컨텍스트를 효율적으로 관리하는 슬라이딩 윈도우 기법을 배웁니다.

## 학습 목표
- 멀티턴 대화 히스토리 관리
- 메모리 효율적 컨텍스트 유지
- 중요한 정보 보존 전략

## 설치

```bash
cd examples/01-basic/sliding-window
pip install -r requirements.txt
```

## 예제

### 1. Conversation Window (conversation_window.py)
기본적인 대화 윈도우 관리

```bash
python conversation_window.py
```

**특징:**
- 최근 N턴만 유지
- 시스템 프롬프트 항상 보존
- 토큰 예산 자동 관리

### 2. Document Chunks (document_chunks.py)
긴 문서를 청크로 나눠 처리

```bash
python document_chunks.py
```

**특징:**
- 오버랩 청킹
- 문서 경계 보존
- 순차적 처리

### 3. Demo Chatbot (demo_chatbot.py)
실제 챗봇에서 슬라이딩 윈도우 적용

```bash
python demo_chatbot.py
```

**특징:**
- 인터랙티브 대화
- 실시간 토큰 모니터링
- 자동 윈도우 조절

**참고:** 실제 LLM 호출을 위해서는 `.env` 파일에 API 키 설정 필요

## 전략 비교

| 전략 | 메모리 사용 | 품질 | 복잡도 |
|------|------------|------|--------|
| Fixed Window | 낮음 | 중간 | 낮음 |
| Token-aware | 중간 | 높음 | 중간 |
| Importance-based | 높음 | 매우 높음 | 높음 |

## 예상 출력

```
==========================================================
                CONVERSATION WINDOW MANAGER
==========================================================

Configuration:
  Max turns: 5
  Max tokens: 4000
  System prompt: 45 tokens

Turn 1:
  User: Hello!
  Tokens in window: 47 (1.2%)

Turn 2:
  User: How are you?
  Tokens in window: 62 (1.6%)

Turn 5:
  User: Tell me about context engineering
  Tokens in window: 234 (5.9%)

Turn 6 (window full):
  Removing oldest turn (Turn 1)
  Tokens in window: 215 (5.4%)
```

## 다음 단계
- [Context Truncation](../context-truncation/) - 기본 절단 기법
- [Token Counting](../token-counting/) - 정확한 토큰 계산
- [Multi-turn Management](../../../docs/03-advanced-patterns/multi-turn-context-mgmt.md) - 고급 멀티턴 전략

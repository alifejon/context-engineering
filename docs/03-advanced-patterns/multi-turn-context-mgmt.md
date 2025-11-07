# 멀티턴 컨텍스트 관리

## 개요
대화가 길어질수록 컨텍스트 윈도우가 쌓입니다. 효과적인 멀티턴 관리가 필수입니다.

## 전략

### 1. 슬라이딩 윈도우
```python
def sliding_window_context(history: list, max_turns: int = 5):
    """최근 N턴만 유지"""
    return history[-max_turns:]
```

### 2. 요약 기반 관리
```python
def summarize_old_context(history: list):
    """오래된 대화는 요약"""
    if len(history) > 10:
        old_messages = history[:-5]
        summary = llm_summarize(old_messages)
        recent = history[-5:]
        return [{"role": "system", "content": f"Previous context: {summary}"}] + recent
    return history
```

### 3. 중요도 기반 선택
```python
def importance_based_selection(history: list, max_tokens: int):
    """중요한 턴만 선택"""
    scored = [(msg, calculate_importance(msg)) for msg in history]
    sorted_msgs = sorted(scored, key=lambda x: x[1], reverse=True)

    selected = []
    total_tokens = 0
    for msg, score in sorted_msgs:
        tokens = count_tokens(msg["content"])
        if total_tokens + tokens <= max_tokens:
            selected.append(msg)
            total_tokens += tokens

    return selected
```

## 요약
긴 대화는 요약, 슬라이딩 윈도우, 중요도 기반 선택으로 관리

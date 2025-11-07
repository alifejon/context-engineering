# 컨텍스트 윈도우 관리

## 개요

컨텍스트 윈도우는 LLM이 한 번에 처리할 수 있는 토큰의 최대 개수입니다. 효과적인 컨텍스트 윈도우 관리는 Context Engineering의 핵심입니다.

## 컨텍스트 윈도우 이해하기

### 주요 LLM 모델의 컨텍스트 윈도우

| Model | Context Window | Input 비용 | Output 비용 | 특징 |
|-------|---------------|-----------|------------|------|
| GPT-3.5-turbo | 16K | $0.0015/1K | $0.002/1K | 빠르고 저렴 |
| GPT-4 | 8K | $0.03/1K | $0.06/1K | 높은 품질 |
| GPT-4-32K | 32K | $0.06/1K | $0.12/1K | 긴 컨텍스트 |
| GPT-4-turbo | 128K | $0.01/1K | $0.03/1K | 균형잡힌 선택 |
| Claude 3 Opus | 200K | $0.015/1K | $0.075/1K | 매우 긴 컨텍스트 |
| Claude 3 Sonnet | 200K | $0.003/1K | $0.015/1K | 비용 효율적 |
| Gemini 1.5 Pro | 1M | $0.00125/1K | $0.005/1K | 초장문 |

### 실제 사용 가능한 윈도우

```python
# 명목상 컨텍스트 윈도우 vs 실제 사용 가능 윈도우
nominal_window = 8000  # 예: GPT-4

# 실제 사용 가능 = 명목상 - 오버헤드
actual_usable = nominal_window - (
    system_prompt_tokens +      # 200-500 tokens
    output_buffer +              # 1000-2000 tokens (응답 공간)
    safety_margin                # 200-500 tokens (여유분)
)

# GPT-4 8K 예시:
# 8000 - 500 (system) - 1500 (output) - 300 (margin) = 5700 tokens
```

**주의사항:**
- 출력 토큰도 전체 윈도우에 포함됨
- 시스템 프롬프트, few-shot 예제도 토큰 소비
- 안전 마진 없이 최대치 사용 시 에러 발생 위험

## 토큰 계산 및 추정

### 1. 정확한 토큰 카운팅

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """정확한 토큰 수 계산"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# 예시
text = "Context engineering is essential for LLM applications."
tokens = count_tokens(text)  # 9 tokens
```

### 2. 빠른 토큰 추정

```python
def estimate_tokens(text: str) -> int:
    """빠른 토큰 추정 (정확도 ~85%)"""
    # 영어: 평균 1 token ≈ 4 characters
    # 한글: 평균 1 token ≈ 1.5-2 characters
    return len(text) // 4

def estimate_tokens_korean(text: str) -> int:
    """한글 텍스트 토큰 추정"""
    return len(text) // 2
```

**언어별 토큰 효율:**

```python
# 같은 의미의 문장
english = "Hello, how are you today?"
korean = "안녕하세요, 오늘 기분이 어떠세요?"

print(count_tokens(english))  # ~7 tokens
print(count_tokens(korean))   # ~20 tokens

# 한글은 영어보다 토큰 비효율적!
```

### 3. 메시지 토큰 계산

```python
def count_message_tokens(messages: list, model: str = "gpt-4") -> int:
    """OpenAI 메시지 형식의 토큰 수 계산"""
    encoding = tiktoken.encoding_for_model(model)

    tokens_per_message = 3  # 메시지 구분자 오버헤드
    tokens_per_name = 1     # name 필드 오버헤드

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # 응답 시작 토큰
    return num_tokens

# 예시
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is context engineering?"},
]
total_tokens = count_message_tokens(messages)  # ~19 tokens
```

## 윈도우 관리 전략

### 전략 1: 고정 윈도우 (Fixed Window)

가장 간단한 방법. 항상 동일한 크기의 컨텍스트를 유지.

```python
def fixed_window(documents: list[str], max_tokens: int) -> str:
    """고정 크기 윈도우"""
    context = ""
    total_tokens = 0

    for doc in documents:
        doc_tokens = count_tokens(doc)
        if total_tokens + doc_tokens <= max_tokens:
            context += doc + "\n\n"
            total_tokens += doc_tokens
        else:
            break  # 윈도우 초과 시 중단

    return context

# 사용 예시
docs = retrieve_documents(query, k=20)
context = fixed_window(docs, max_tokens=4000)
```

**장점:**
- 구현이 간단
- 예측 가능한 비용

**단점:**
- 유연성 부족
- 중요한 정보가 잘릴 수 있음

### 전략 2: 슬라이딩 윈도우 (Sliding Window)

멀티턴 대화에서 최근 N개 메시지만 유지.

```python
def sliding_window(
    conversation_history: list[dict],
    max_tokens: int,
    keep_system_prompt: bool = True
) -> list[dict]:
    """슬라이딩 윈도우로 대화 관리"""
    if not conversation_history:
        return []

    # 시스템 프롬프트는 항상 유지
    system_messages = [msg for msg in conversation_history
                       if msg["role"] == "system"]
    other_messages = [msg for msg in conversation_history
                      if msg["role"] != "system"]

    # 최근 메시지부터 추가
    selected_messages = []
    current_tokens = count_message_tokens(system_messages)

    for msg in reversed(other_messages):
        msg_tokens = count_message_tokens([msg])
        if current_tokens + msg_tokens <= max_tokens:
            selected_messages.insert(0, msg)
            current_tokens += msg_tokens
        else:
            break

    return system_messages + selected_messages

# 사용 예시
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Message 1"},
    {"role": "assistant", "content": "Response 1"},
    {"role": "user", "content": "Message 2"},
    {"role": "assistant", "content": "Response 2"},
    {"role": "user", "content": "Message 3"},  # 가장 최근
]

windowed = sliding_window(conversation, max_tokens=1000)
# → 시스템 프롬프트 + 최근 N개 메시지
```

**장점:**
- 멀티턴 대화에 적합
- 최신 정보 유지

**단점:**
- 오래된 중요 정보 손실

### 전략 3: 우선순위 기반 윈도우 (Priority-based Window)

중요도에 따라 컨텍스트 선택.

```python
def priority_based_window(
    contexts: list[dict],  # {"content": str, "priority": int, "tokens": int}
    max_tokens: int
) -> str:
    """우선순위 기반 윈도우"""
    # 우선순위로 정렬 (높은 순)
    sorted_contexts = sorted(contexts, key=lambda x: x["priority"], reverse=True)

    selected = []
    total_tokens = 0

    for ctx in sorted_contexts:
        if total_tokens + ctx["tokens"] <= max_tokens:
            selected.append(ctx)
            total_tokens += ctx["tokens"]
        else:
            # 남은 공간에 맞게 압축 시도
            remaining = max_tokens - total_tokens
            if remaining > 100:  # 최소 100 토큰은 있어야 의미있음
                compressed = compress_context(ctx["content"], remaining)
                selected.append({
                    "content": compressed,
                    "priority": ctx["priority"],
                    "tokens": count_tokens(compressed)
                })
            break

    # 우선순위 순서로 재정렬하여 반환
    selected.sort(key=lambda x: x["priority"], reverse=True)
    return "\n\n".join([ctx["content"] for ctx in selected])

# 사용 예시
contexts = [
    {
        "content": current_query,
        "priority": 10,  # 최우선
        "tokens": count_tokens(current_query)
    },
    {
        "content": user_profile,
        "priority": 8,
        "tokens": count_tokens(user_profile)
    },
    {
        "content": relevant_docs,
        "priority": 6,
        "tokens": count_tokens(relevant_docs)
    },
    {
        "content": general_knowledge,
        "priority": 3,
        "tokens": count_tokens(general_knowledge)
    },
]

optimized_context = priority_based_window(contexts, max_tokens=4000)
```

**장점:**
- 중요한 정보 우선 보장
- 유연한 컨텍스트 구성

**단점:**
- 우선순위 결정이 필요
- 구현 복잡도 증가

### 전략 4: 동적 윈도우 (Dynamic Window)

쿼리 복잡도에 따라 윈도우 크기 조절.

```python
def dynamic_window(
    query: str,
    available_contexts: list[str],
    base_max_tokens: int
) -> str:
    """쿼리 복잡도에 따른 동적 윈도우"""
    # 쿼리 복잡도 분석
    complexity = analyze_query_complexity(query)

    # 복잡도에 따라 윈도우 크기 조절
    if complexity == "simple":
        max_tokens = base_max_tokens * 0.5  # 간단한 쿼리는 적은 컨텍스트
    elif complexity == "medium":
        max_tokens = base_max_tokens * 0.8
    else:  # complex
        max_tokens = base_max_tokens * 1.0  # 복잡한 쿼리는 많은 컨텍스트

    return fixed_window(available_contexts, int(max_tokens))

def analyze_query_complexity(query: str) -> str:
    """쿼리 복잡도 분석"""
    # 간단한 휴리스틱
    words = query.split()

    if len(words) < 5:
        return "simple"
    elif len(words) < 15:
        return "medium"
    else:
        return "complex"

    # 더 정교한 분석 가능:
    # - 질문 개수 (and, or 등)
    # - 전문 용어 포함 여부
    # - 다단계 추론 필요 여부
```

**장점:**
- 효율적인 토큰 사용
- 쿼리에 맞는 최적화

**단점:**
- 복잡도 판단이 어려울 수 있음

## 실전 윈도우 관리 패턴

### 패턴 1: 계층적 컨텍스트 구조

```python
class HierarchicalContextManager:
    """계층적 컨텍스트 관리"""

    def __init__(self, total_budget: int):
        self.total_budget = total_budget
        self.allocations = {
            "system_prompt": 0.05,      # 5%
            "user_context": 0.15,        # 15%
            "conversation_history": 0.20, # 20%
            "retrieved_knowledge": 0.50,  # 50%
            "output_buffer": 0.10,       # 10%
        }

    def allocate_tokens(self) -> dict:
        """토큰 예산 할당"""
        return {
            category: int(self.total_budget * ratio)
            for category, ratio in self.allocations.items()
        }

    def build_context(self, **contexts) -> dict:
        """컨텍스트 구축"""
        budget = self.allocate_tokens()

        return {
            "system": self.fit_to_budget(
                contexts.get("system_prompt", ""),
                budget["system_prompt"]
            ),
            "user": self.fit_to_budget(
                contexts.get("user_context", ""),
                budget["user_context"]
            ),
            "history": sliding_window(
                contexts.get("conversation_history", []),
                budget["conversation_history"]
            ),
            "knowledge": self.fit_to_budget(
                contexts.get("retrieved_knowledge", ""),
                budget["retrieved_knowledge"]
            ),
        }

    def fit_to_budget(self, content: str, budget: int) -> str:
        """예산에 맞게 조정"""
        tokens = count_tokens(content)
        if tokens <= budget:
            return content

        # 예산 초과 시 압축
        return compress_to_budget(content, budget)

# 사용 예시
manager = HierarchicalContextManager(total_budget=8000)
context = manager.build_context(
    system_prompt="You are a helpful assistant.",
    user_context=user_profile,
    conversation_history=chat_history,
    retrieved_knowledge=rag_results
)
```

### 패턴 2: 적응형 컨텍스트 관리

```python
class AdaptiveContextManager:
    """적응형 컨텍스트 관리"""

    def __init__(self):
        self.usage_history = []
        self.performance_metrics = {}

    def optimize_context(
        self,
        query: str,
        available_contexts: list[dict]
    ) -> str:
        """과거 데이터 기반 최적화"""
        # 유사한 과거 쿼리 찾기
        similar_queries = self.find_similar_queries(query)

        if similar_queries:
            # 과거 성공 패턴 사용
            optimal_size = self.get_optimal_size(similar_queries)
            optimal_types = self.get_optimal_types(similar_queries)

            # 필터링 및 크기 조절
            filtered = [ctx for ctx in available_contexts
                       if ctx["type"] in optimal_types]
            return self.build_context(filtered, optimal_size)
        else:
            # 기본 전략 사용
            return self.default_strategy(available_contexts)

    def record_usage(
        self,
        query: str,
        context_size: int,
        context_types: list[str],
        performance_score: float
    ):
        """사용 기록 저장"""
        self.usage_history.append({
            "query": query,
            "context_size": context_size,
            "context_types": context_types,
            "performance": performance_score,
            "timestamp": datetime.now()
        })
```

## 멀티모달 컨텍스트 관리

이미지, 오디오 등 멀티모달 입력 시 토큰 계산:

```python
def count_multimodal_tokens(inputs: dict) -> int:
    """멀티모달 입력의 토큰 계산"""
    total = 0

    # 텍스트
    if "text" in inputs:
        total += count_tokens(inputs["text"])

    # 이미지 (GPT-4V 기준)
    if "images" in inputs:
        for image in inputs["images"]:
            width, height = image["size"]
            # 이미지는 고정 토큰 + 타일 기반 계산
            total += 85  # 기본 토큰
            total += 170 * calculate_tiles(width, height)

    # 오디오 (Whisper 등)
    if "audio" in inputs:
        duration_seconds = inputs["audio"]["duration"]
        # 대략 1초당 2-3 토큰
        total += int(duration_seconds * 2.5)

    return total

def calculate_tiles(width: int, height: int) -> int:
    """이미지 타일 수 계산 (GPT-4V)"""
    # 512x512 타일로 분할
    tiles_w = (width + 511) // 512
    tiles_h = (height + 511) // 512
    return tiles_w * tiles_h
```

## 모니터링 및 디버깅

```python
class ContextWindowMonitor:
    """컨텍스트 윈도우 모니터링"""

    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.warnings = []

    def check_context(self, context: dict) -> dict:
        """컨텍스트 검사"""
        total_tokens = sum(
            count_tokens(str(v)) for v in context.values()
        )

        utilization = total_tokens / self.max_tokens

        report = {
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": f"{utilization:.1%}",
            "status": self.get_status(utilization),
            "breakdown": {
                key: count_tokens(str(value))
                for key, value in context.items()
            }
        }

        # 경고 생성
        if utilization > 0.95:
            report["warning"] = "위험: 윈도우 거의 가득 참"
        elif utilization > 0.85:
            report["warning"] = "주의: 윈도우 85% 이상 사용"

        return report

    def get_status(self, utilization: float) -> str:
        if utilization < 0.7:
            return "✓ 정상"
        elif utilization < 0.85:
            return "⚠ 주의"
        else:
            return "✗ 위험"

# 사용 예시
monitor = ContextWindowMonitor(max_tokens=8000)
report = monitor.check_context({
    "system": system_prompt,
    "user": user_query,
    "history": conversation_history,
    "documents": retrieved_docs
})

print(report)
# {
#     "total_tokens": 6500,
#     "max_tokens": 8000,
#     "utilization": "81.3%",
#     "status": "⚠ 주의",
#     "breakdown": {
#         "system": 250,
#         "user": 150,
#         "history": 2100,
#         "documents": 4000
#     }
# }
```

## 실전 팁

### 1. 항상 여유분 확보
```python
safe_max_tokens = nominal_max - 1000  # 최소 1000 토큰 여유
```

### 2. 출력 길이 고려
```python
expected_output_tokens = 500  # 예상 응답 길이
max_input_tokens = total_window - expected_output_tokens - safety_margin
```

### 3. 언어별 토큰 효율 고려
```python
# 한글 문서는 더 많은 토큰 소비
korean_doc_tokens = len(korean_text) // 2
english_doc_tokens = len(english_text) // 4
```

### 4. 정기적인 토큰 사용량 모니터링
```python
# 로깅
log_token_usage(
    input_tokens=input_count,
    output_tokens=output_count,
    total_cost=calculated_cost
)
```

## 다음 단계

- [토큰 경제학](./token-economics.md) - 비용 최적화 전략
- [컨텍스트 압축](../02-core-concepts/context-compression.md) - 압축 기법

## 요약

1. **정확한 토큰 카운팅**: tiktoken 사용
2. **적절한 전략 선택**: 사용 사례에 맞는 윈도우 관리
3. **계층적 할당**: 중요도별 토큰 예산 배분
4. **지속적 모니터링**: 토큰 사용량 추적 및 최적화

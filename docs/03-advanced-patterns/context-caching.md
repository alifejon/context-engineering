# 컨텍스트 캐싱 전략

## 개요

컨텍스트 캐싱은 자주 사용되는 컨텍스트를 재사용하여 LLM 호출 비용과 지연 시간을 크게 줄이는 기법입니다.

## 캐싱 전략

### 1. 시스템 프롬프트 캐싱
```python
class SystemPromptCache:
    """시스템 프롬프트 캐싱 (Anthropic Prompt Caching 활용)"""

    def __init__(self):
        self.cached_prompts = {}

    def get_cached_prompt(self, key: str) -> dict:
        """캐시된 프롬프트 사용"""
        return {
            "role": "system",
            "content": self.cached_prompts.get(key, ""),
            "cache_control": {"type": "ephemeral"}  # Anthropic 캐싱
        }
```

### 2. 문서 캐싱
```python
class DocumentCache:
    """자주 사용되는 문서 캐싱"""

    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl

    def get_or_retrieve(self, doc_id: str, retrieval_fn: callable) -> str:
        """캐시 또는 검색"""
        if doc_id in self.cache:
            entry = self.cache[doc_id]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["content"]

        # 캐시 미스 - 검색
        content = retrieval_fn(doc_id)
        self.cache[doc_id] = {
            "content": content,
            "timestamp": time.time()
        }
        return content
```

### 3. 응답 캐싱
```python
import hashlib

class ResponseCache:
    """동일 쿼리 응답 캐싱"""

    def __init__(self):
        self.cache = {}

    def get_cache_key(self, query: str, context: str) -> str:
        """캐시 키 생성"""
        combined = f"{query}||{context}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, query: str, context: str) -> str:
        """캐시 조회"""
        key = self.get_cache_key(query, context)
        return self.cache.get(key)

    def set(self, query: str, context: str, response: str):
        """캐시 저장"""
        key = self.get_cache_key(query, context)
        self.cache[key] = response
```

## Anthropic Prompt Caching 활용

```python
# Anthropic의 Prompt Caching 기능 활용 예시
def create_cached_context(knowledge_base: str, user_query: str):
    """
    Anthropic Prompt Caching으로 큰 컨텍스트 재사용
    - 캐시된 토큰: 90% 비용 절감
    - 캐시 TTL: 5분
    """
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Knowledge Base:\n{knowledge_base}",
                    "cache_control": {"type": "ephemeral"}  # 이 부분 캐싱
                },
                {
                    "type": "text",
                    "text": f"Query: {user_query}"
                }
            ]
        }
    ]
    return messages

# 비용 절감 효과:
# 첫 요청: 10,000 tokens × $0.015/1K = $0.15
# 캐시 히트: 10,000 tokens × $0.0015/1K = $0.015 (90% 절감!)
```

## 요약
캐싱으로 40-90% 비용 절감 가능. 특히 반복적인 컨텍스트에 효과적.

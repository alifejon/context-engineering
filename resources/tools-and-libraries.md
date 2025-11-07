# 도구 및 라이브러리

## 필수 라이브러리

### 1. 토큰 카운팅
```bash
pip install tiktoken
```
- OpenAI 공식 토큰 카운팅 라이브러리
- GPT 모델의 정확한 토큰 수 계산

### 2. 벡터 검색
```bash
pip install chromadb
pip install faiss-cpu
pip install qdrant-client
```
- Chroma: 간단한 임베딩 DB
- FAISS: Meta의 고성능 유사도 검색
- Qdrant: 프로덕션급 벡터 DB

### 3. LLM 프레임워크
```bash
pip install langchain langchain-openai
pip install llama-index
```
- LangChain: RAG 및 체인 구성
- LlamaIndex: 데이터 인덱싱 및 쿼리

### 4. 텍스트 처리
```bash
pip install scikit-learn
pip install sentence-transformers
pip install transformers
```
- scikit-learn: TF-IDF, 유사도 계산
- sentence-transformers: 임베딩 생성
- transformers: Hugging Face 모델

## Context Engineering 도구

### 1. 압축 도구
```python
# LongLLMLingua - 컨텍스트 압축
from llmlingua import PromptCompressor

compressor = PromptCompressor()
compressed = compressor.compress_prompt(
    context,
    target_token=2000
)
```

### 2. 리랭킹 도구
```python
# Cohere Rerank
import cohere

co = cohere.Client(api_key)
results = co.rerank(
    query=query,
    documents=documents,
    top_n=5,
    model='rerank-english-v2.0'
)
```

### 3. 모니터링 도구
```bash
# LangSmith
pip install langsmith

# Helicone (OpenAI 프록시)
# 설정만으로 자동 로깅
```

## 벡터 데이터베이스 비교

| DB | 타입 | 성능 | 확장성 | 가격 |
|----|------|------|--------|------|
| Chroma | 로컬/임베디드 | 중간 | 제한적 | 무료 |
| FAISS | 로컬 | 높음 | 중간 | 무료 |
| Pinecone | 클라우드 | 높음 | 높음 | 유료 |
| Qdrant | 셀프호스팅/클라우드 | 높음 | 높음 | 무료/유료 |
| Weaviate | 셀프호스팅/클라우드 | 높음 | 높음 | 무료/유료 |

## 임베딩 모델 비교

| 모델 | 차원 | 성능 | 다국어 | 비용 |
|------|------|------|--------|------|
| OpenAI ada-002 | 1536 | 높음 | 예 | $0.0001/1K tokens |
| Cohere v3 | 1024 | 높음 | 예 | $0.0001/1K tokens |
| Sentence-BERT | 384-768 | 중간 | 제한적 | 무료 |
| Multilingual-E5 | 768 | 높음 | 예 | 무료 |

## 개발 환경 설정

### Python 환경
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 필수 패키지 설치
pip install -r requirements.txt
```

### requirements.txt
```
openai>=1.0.0
anthropic>=0.8.0
tiktoken>=0.5.0
langchain>=0.1.0
chromadb>=0.4.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0
```

## 프로덕션 도구

### 캐싱
- Redis: 응답 캐싱
- Memcached: 분산 캐싱

### 모니터링
- Prometheus + Grafana: 메트릭
- ELK Stack: 로그 분석
- Sentry: 에러 추적

### API 게이트웨이
- Kong: API 관리
- Nginx: 로드 밸런싱
- Traefik: 컨테이너 라우팅

## 유용한 CLI 도구

```bash
# 토큰 카운팅
pip install tiktoken-cli
tiktoken-count "your text here"

# JSON 처리
pip install jq

# HTTP 테스팅
pip install httpie
```

## 다음 단계

실제 사용 예제는 [examples](../examples/) 디렉토리 참고

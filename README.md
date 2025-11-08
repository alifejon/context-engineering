# Context Engineering

프롬프트 엔지니어링과 RAG 개발자를 위한 Context Engineering 학습 자료

## 📖 소개

**Context Engineering**은 LLM 애플리케이션에서 컨텍스트 윈도우를 효율적으로 관리하고 최적화하는 체계적인 접근 방식입니다. 프롬프트 엔지니어링(PE)과 RAG를 이미 알고 있다면, Context Engineering은 다음 단계로 나아가는 핵심 스킬입니다.

### 왜 Context Engineering인가?

**프롬프트 엔지니어링**은 "무엇을" 물어볼지에 집중합니다.
**RAG**는 "어떻게" 관련 정보를 검색할지에 집중합니다.
**Context Engineering**은 "어떻게" 컨텍스트를 효율적으로 구성하고 관리할지에 집중합니다.

```
Prompt Engineering: "좋은 질문 만들기"
         ↓
RAG: "관련 문서 찾기"
         ↓
Context Engineering: "컨텍스트 최적화 및 관리"
         ↓
LLM Response
```

### 주요 차이점

| 측면 | Prompt Engineering | RAG | Context Engineering |
|------|-------------------|-----|---------------------|
| **초점** | 프롬프트 설계 | 문서 검색 | 컨텍스트 관리 |
| **목표** | 명확한 지시 | 관련 정보 검색 | 효율적 컨텍스트 활용 |
| **최적화 대상** | 프롬프트 품질 | 검색 정확도 | 토큰 사용, 응답 품질 |
| **핵심 과제** | 모호성 제거 | 관련성 평가 | 윈도우 관리, 압축 |

## 🎯 학습 대상

이 자료는 다음과 같은 분들에게 적합합니다:

- ✅ 프롬프트 엔지니어링 기초를 이해하고 있는 개발자
- ✅ RAG 시스템을 구축해본 경험이 있는 개발자
- ✅ LLM 애플리케이션의 성능과 비용을 최적화하고 싶은 개발자
- ✅ 프로덕션 환경에서 안정적인 LLM 서비스를 운영하고 싶은 개발자

## 📚 학습 경로

### 🎓 교육용 학습 경로 (Learning Track)

**목표**: Context Engineering 개념과 기법 이해하기

### 1️⃣ 기초 개념 (Fundamentals)
- [Context Engineering이란?](docs/01-fundamentals/what-is-context-engineering.md)
- [컨텍스트 윈도우 관리](docs/01-fundamentals/context-window-management.md)
- [토큰 경제학](docs/01-fundamentals/token-economics.md)

### 2️⃣ 핵심 개념 (Core Concepts)
- [컨텍스트 압축](docs/02-core-concepts/context-compression.md)
- [컨텍스트 우선순위화](docs/02-core-concepts/context-prioritization.md)
- [동적 컨텍스트 구성](docs/02-core-concepts/dynamic-context-assembly.md)
- [컨텍스트 품질 관리](docs/02-core-concepts/context-quality-control.md)

### 3️⃣ 고급 패턴 (Advanced Patterns)
- [멀티턴 컨텍스트 관리](docs/03-advanced-patterns/multi-turn-context-mgmt.md)
- [계층적 컨텍스트 구조](docs/03-advanced-patterns/hierarchical-context.md)
- [컨텍스트 캐싱 전략](docs/03-advanced-patterns/context-caching.md)
- [하이브리드 검색 패턴](docs/03-advanced-patterns/hybrid-retrieval.md)

### 4️⃣ 실전 가이드 (Practical Guides)
- [컨텍스트 문제 디버깅](docs/04-practical-guides/debugging-context-issues.md)
- [성능 최적화](docs/04-practical-guides/performance-optimization.md)
- [모범 사례](docs/04-practical-guides/best-practices.md)

---

### 🏭 프로덕션 학습 경로 (Production Track)

**목표**: 실제 회사에서 사용 가능한 시스템 구축하기

**📖 [10주 프로덕션 학습 로드맵](learning-path/README.md)** ⭐ **NEW!**

#### 전체 개요
- **기간**: 10주 (Part-time) 또는 6주 (Full-time)
- **시간 투자**: 주당 20-40시간
- **난이도**: ⭐⭐⭐⭐ (중급-고급)
- **산출물**: 프로덕션 배포 가능한 완전한 API 시스템

#### 주차별 학습 내용

| Week | 주제 | 핵심 내용 | 난이도 |
|------|------|-----------|--------|
| 1-2 | [Foundation & Stability](learning-path/week-01-02-stability/) | Error handling, Logging, Testing | ⭐⭐⭐ |
| 3-4 | [Data & Caching](learning-path/week-03-04-data-caching/) | PostgreSQL, Redis, Migrations | ⭐⭐⭐ |
| 5-6 | API Server | FastAPI, Authentication, Rate limiting | ⭐⭐⭐⭐ |
| 7-8 | Deployment & Monitoring | Docker, K8s, Prometheus, Grafana | ⭐⭐⭐⭐ |
| 9-10 | Advanced & Optimization | Async, Performance, Security | ⭐⭐⭐⭐⭐ |
| 11-12 | [Final Project](learning-path/final-project/) | Complete Production System | ⭐⭐⭐⭐⭐ |

#### 학습 성과

10주 완료 시:
- ✅ 프로덕션 수준의 에러 핸들링
- ✅ 구조화된 로깅 및 모니터링
- ✅ 80%+ 테스트 커버리지
- ✅ FastAPI 기반 REST API
- ✅ PostgreSQL + Redis 데이터 계층
- ✅ Docker/Kubernetes 배포
- ✅ CI/CD 파이프라인
- ✅ 실시간 모니터링 대시보드

#### 프로덕션 준비 평가

**현재 상태 평가**: [Production Readiness Evaluation](PRODUCTION_READINESS_EVALUATION.md)
- 교육용 코드: 9/10 ✅
- 프로덕션 코드: 4/10 ❌ → **학습 경로로 10/10 달성 가능!**

#### 프로덕션 예제 코드

- [에러 핸들링 & 재시도](examples/production-ready/core/error_handling.py) - Circuit breaker, Retry logic
- [구조화된 로깅](examples/production-ready/core/logging_config.py) - JSON logs, Request tracing
- [프로덕션 LLM 클라이언트](examples/production-ready/clients/llm_client.py) - 실제 OpenAI 연동
- [테스트 예제](examples/production-ready/tests/) - Unit & Integration tests

#### 빠른 시작

```bash
# Week 1-2 시작하기
cd learning-path/week-01-02-stability
cat README.md

# 환경 설정
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 첫 번째 실습
python exercises/01_error_handling_basic.py
```

---

### 📊 학습 경로 선택 가이드

| 특성 | 교육용 경로 | 프로덕션 경로 |
|------|-------------|---------------|
| **목표** | 개념 이해 및 기법 학습 | 실전 시스템 구축 |
| **기간** | 4주 | 10-12주 |
| **난이도** | ⭐⭐ | ⭐⭐⭐⭐ |
| **산출물** | 프로토타입, 예제 | 프로덕션 배포 시스템 |
| **코드 품질** | 학습용 (70%) | 프로덕션 수준 (100%) |
| **테스트** | 선택적 | 필수 (80%+ 커버리지) |
| **배포** | 로컬 실행 | K8s 프로덕션 배포 |
| **모니터링** | print() | Prometheus + Grafana |
| **추천 대상** | 초보자, 빠른 학습 | 실무 적용, 포트폴리오 |

**💡 추천 학습 순서**:
1. 교육용 경로로 기초 다지기 (4주)
2. 프로덕션 경로로 실전 역량 쌓기 (10주)
3. 실제 프로젝트에 적용하기

## 💻 실습 예제

### 기초 예제
- [컨텍스트 절단](examples/01-basic/context-truncation/)
- [슬라이딩 윈도우](examples/01-basic/sliding-window/)
- [토큰 카운팅](examples/01-basic/token-counting/)

### 압축 기법
- [요약 기반 압축](examples/02-compression/summarization-based/)
- [의미적 압축](examples/02-compression/semantic-compression/)
- [하이브리드 압축](examples/02-compression/hybrid-compression/)

### 우선순위화
- [관련성 점수화](examples/03-prioritization/relevance-scoring/)
- [최신성 가중치](examples/03-prioritization/recency-weighting/)
- [중요도 랭킹](examples/03-prioritization/importance-ranking/)

### 동적 어셈블리
- [쿼리 인식 컨텍스트](examples/04-dynamic-assembly/query-aware-context/)
- [적응형 검색](examples/04-dynamic-assembly/adaptive-retrieval/)
- [컨텍스트 라우팅](examples/04-dynamic-assembly/context-routing/)

### 프로덕션 패턴
- [컨텍스트 모니터링](examples/05-production-patterns/context-monitoring/)
- [비용 최적화](examples/05-production-patterns/cost-optimization/)
- [A/B 테스트](examples/05-production-patterns/ab-testing-contexts/)

## 🎓 튜토리얼

1. [프롬프트 엔지니어링에서 컨텍스트 엔지니어링으로](tutorials/01-from-prompt-to-context.md)
2. [RAG에 Context Engineering 적용하기](tutorials/02-enhancing-rag-with-ce.md)
3. [컨텍스트 최적화기 구축하기](tutorials/03-building-context-optimizer.md)
4. [프로덕션 배포 가이드](tutorials/04-production-deployment.md)

## 🛠️ 도구

- [컨텍스트 분석기](tools/context-analyzer/) - 컨텍스트 품질 분석 도구
- [토큰 최적화기](tools/token-optimizer/) - 토큰 사용량 최적화 도구
- [벤치마킹](tools/benchmarking/) - 성능 측정 도구

## 📊 사례 연구

- [챗봇 컨텍스트 관리](case-studies/chatbot-context-management.md)
- [문서 QA 최적화](case-studies/document-qa-optimization.md)
- [코드 어시스턴트 컨텍스트](case-studies/code-assistant-context.md)

## 📖 참고 자료

- [연구 논문](resources/research-papers.md)
- [도구 및 라이브러리](resources/tools-and-libraries.md)
- [커뮤니티 리소스](resources/community-resources.md)

## 🏋️ 연습 문제

- [연습 문제 1: 컨텍스트 분석](exercises/exercise-01-context-analysis.md)
- [연습 문제 2: 압축 구현](exercises/exercise-02-compression.md)
- [솔루션](exercises/solutions/)

## 🚀 빠른 시작

### 전제 조건
```bash
# Python 3.8+
python --version

# 필요한 패키지 설치
pip install openai anthropic tiktoken langchain chromadb
```

### 첫 번째 예제 실행
```bash
cd examples/01-basic/token-counting
python example.py
```

## 📈 학습 로드맵

```
Week 1: 기초 개념 + 기본 예제
  ├─ Context Engineering 이해
  ├─ 토큰 경제학
  └─ 기본 예제 실습

Week 2: 핵심 개념 + 압축 기법
  ├─ 컨텍스트 압축
  ├─ 우선순위화
  └─ 압축 예제 실습

Week 3: 고급 패턴 + 동적 구성
  ├─ 멀티턴 관리
  ├─ 캐싱 전략
  └─ 동적 어셈블리 실습

Week 4: 프로덕션 + 최적화
  ├─ 성능 최적화
  ├─ 모니터링
  └─ 프로덕션 배포
```

## 💡 핵심 인사이트

> "프롬프트 엔지니어링은 질문을 잘하는 것이고, RAG는 답을 잘 찾는 것이며, Context Engineering은 대화를 잘 관리하는 것입니다."

### Context Engineering의 3대 원칙

1. **효율성 (Efficiency)**: 필요한 정보만 포함하고 불필요한 토큰 제거
2. **관련성 (Relevance)**: 쿼리와 가장 관련성 높은 컨텍스트 우선
3. **적응성 (Adaptability)**: 상황에 따라 동적으로 컨텍스트 구성

## 🤝 기여하기

이 프로젝트는 오픈소스입니다. 기여를 환영합니다!

- 버그 리포트
- 새로운 예제 추가
- 문서 개선
- 번역

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📬 연락처

질문이나 제안사항이 있으시면 이슈를 등록해주세요.

---

**Happy Context Engineering! 🚀**

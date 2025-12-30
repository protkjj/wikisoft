# Phase 2 Migration Guide (v3.0)

목표: 인메모리 에이전트를 지속 가능한 프로덕션 아키텍처로 확장
- 메모리: In-memory → Redis (단기)
- 학습/검색: Few-shot + Vector DB (Chroma) (중기)
- 오케스트레이션: LangChain/LlamaIndex 통합 (중기)

## 1) Redis 메모리로 이관

### 설계
- 기존 `internal/agent/memory.py` 유지 → 인터페이스 호환
- 구현 교체: `MemorySystem`의 저장/검색/통계 로직을 Redis Key-Value로 매핑

### 키 설계
- `mem:{type}:{id}` → Entry JSON
- `idx:{type}` → ID 리스트 (Sorted set: confidence/last_used 가중치)
- `stat:usage` → 누적 카운트

### 단계
1. `redis` 설치/연결 (`REDIS_URL` 환경변수)
2. 새 파일 `internal/agent/memory_redis.py` 구현 (동일 API)
3. 팩토리 함수 `get_memory()`가 환경변수로 Redis/메모리 선택

### 샘플 코드
```python
# internal/agent/memory_factory.py
import os
from .memory import MemorySystem as MemoryInMemory
from .memory_redis import MemorySystem as MemoryRedis

def get_memory():
    if os.getenv("USE_REDIS", "false").lower() == "true":
        return MemoryRedis(max_entries=100000)
    return MemoryInMemory(max_entries=1000)
```

## 2) Vector DB (Chroma) 통합

### 목적
- 과거 패턴/오류/룰을 임베딩하여 유사 질의 검색
- 프롬프트 few-shot에 상위 유사 사례 자동 삽입

### 단계
1. `chromadb` 설치, 컬렉션 `wikisoft_patterns`
2. 메모리 export 시 `id`, `type`, `key`, `data`를 텍스트화하여 임베딩 저장
3. 검색 API 추가: `search_embeddings(query, top_k=5)` → IDs 반환

### 샘플
```python
from chromadb import Client
client = Client()
col = client.get_or_create_collection("wikisoft_patterns")
col.add(documents=["salary > 0"], ids=["p1"], metadatas=[{"type":"pattern"}])
res = col.query(query_texts=["salary rule"], n_results=3)
```

## 3) LangChain/LlamaIndex로 오케스트레이션

### 목적
- Tool 선택/호출/관찰을 LLM Agent로 일반화
- 프롬프트 템플릿/메모리/리트리벌 구성 분리

### 단계
1. LangChain `Tool` 래퍼 생성 (parser/validator/analyzer)
2. `AgentExecutor`로 ReACT loop 구성
3. PromptConfig를 LangChain 템플릿으로 변환

### 주의
- 현재 하드코딩 질문/스키마/프롬프트는 변경하지 말고 래핑만
- 외부 설정은 `load_from_file()`로 병합(덮어쓰기 금지)

## 4) 운영 고려사항

- Observability: 구조화 로그 유지 (`external/api/main.py`), request_id 포함
- 성능: `/batch-validate` 비동기화 (Background tasks, streaming progress)
- 보안: API 토큰/Redis 인증, 민감 데이터 마스킹 유지

## 5) 체크리스트

- [ ] USE_REDIS=true로 전환 시 정상 동작
- [ ] Chroma 컬렉션 생성 및 검색 결과 few-shot 반영
- [ ] LangChain 에이전트 도구 래퍼로 최소 3개 도구 연동
- [ ] 테스트: 기존 16개 + Redis/Chroma 추가 테스트 8개 이상
- [ ] 문서 업데이트: README, OpenAPI, 운영 가이드

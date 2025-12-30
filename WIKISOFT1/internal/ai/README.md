# AI Integration Module

## 📁 구조

```
internal/ai/
├── __init__.py       ← export
├── client.py         ← AIProcessor 클래스
├── prompts.py        ← 프롬프트 템플릿
└── README.md         ← 이 파일
```

## 🎯 목적

**모든 정규화와 검증을 AI(LLM)에게 위임**

## 🚀 사용법

```python
from internal.ai import AIProcessor

ai = AIProcessor(api_key="sk-xxx")
result = ai.normalize_and_validate(df, column_mapping)

print(result["normalized_data"])  # 정규화된 데이터
print(result["errors"])           # 발견된 오류
```

## 📝 TODO

- [ ] OpenAI 클라이언트 초기화
- [ ] normalize_and_validate() 구현
- [ ] 프롬프트 최적화
- [ ] 에러 핸들링
- [ ] 재시도 로직

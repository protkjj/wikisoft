# Training Data

이 폴더는 커스텀 AI 모델 파인튜닝을 위한 학습 데이터를 저장합니다.

## 데이터 구조

각 JSON 파일은 다음 구조를 따릅니다:

```json
{
  "timestamp": "2024-12-31T10:30:00",
  "category": "validation",
  "input": {
    "diagnostic_answers": {"q1": "예", "q2": 60, ...},
    "roster_summary": {"row_count": 52, "headers": [...]}
  },
  "ai_response": {
    "warnings": [...],
    "analysis": "..."
  },
  "human_correction": {
    "warnings": [...],
    "comment": "AI가 놓친 부분..."
  },
  "is_correct": false
}
```

## 카테고리

- `validation`: 검증 결과 분석
- `matching`: 헤더 매칭 판단
- `analysis`: 맥락 분석 및 권장사항
- `error_detection`: 오류 탐지

## 사용법

1. **데이터 수집**: 시스템 사용 중 AI 응답과 사람의 수정 자동 저장
2. **데이터 정제**: 올바른 예시 선별 (`is_correct: true`)
3. **Few-shot 활용**: 프롬프트에 좋은 예시 포함
4. **파인튜닝**: 충분한 데이터 수집 후 모델 파인튜닝

## 파인튜닝 준비

나중에 OpenAI, Claude 등에서 파인튜닝 시:

```python
from internal.ai.knowledge_base import load_training_examples

# 학습 데이터 로드
examples = load_training_examples(category="validation")

# OpenAI 형식으로 변환
training_data = []
for ex in examples:
    if ex["is_correct"] or ex.get("human_correction"):
        training_data.append({
            "messages": [
                {"role": "user", "content": str(ex["input"])},
                {"role": "assistant", "content": str(ex.get("human_correction") or ex["ai_response"])}
            ]
        })
```

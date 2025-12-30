from typing import Dict, List


def create_normalize_prompt(df_sample: List[Dict], diagnostic_answers: Dict[str, str]) -> str:
    """
    데이터 정규화 프롬프트 생성
    
    Args:
        df_sample: 데이터 샘플 (dict 리스트, 마스킹된 상태)
        diagnostic_answers: 초기 진단 질문 답변
    """
    import json
    
    sample_json = json.dumps(df_sample[:5], ensure_ascii=False, indent=2)
    
    q1 = diagnostic_answers.get('q1', '혼합')  # 직원 상태
    q3 = diagnostic_answers.get('q3', '만원')  # 급여 단위
    
    prompt = f"""
## HR 데이터 정규화 요청

### 데이터 샘플 (처음 5행):
{sample_json}

### 고객 정보:
- 직원 상태: {q1}
- 급여 단위: {q3}

### 정규화 규칙:
1. **전화번호**: 01012345678 형식 (11자리, 숫자만)
2. **생년월일**: YYYY-MM-DD 형식
3. **입사일**: YYYY-MM-DD 형식
4. **급여**: 만원 단위 숫자 (쉼표·원·억 제거)

### 응답 형식 (JSON만):
{{
    "normalized_rows": [
        {{
            "row": 0,
            "columns": {{
                "전화": "01012345678",
                "생년월일": "1992-05-15",
                "급여": "5000"
            }},
            "confidence": 0.95
        }}
    ]
}}
"""
    return prompt


def create_questions_prompt(errors: List[Dict], anomalies: List[Dict]) -> str:
    """
    챗봇 질문 생성 프롬프트
    
    Args:
        errors: Layer 1 검증 에러
        anomalies: Layer 2 이상치
    """
    import json
    
    errors_json = json.dumps(errors[:10], ensure_ascii=False, indent=2)
    anomalies_json = json.dumps(anomalies[:10], ensure_ascii=False, indent=2)
    
    prompt = f"""
## HR 데이터 검증 질문 생성

### 검출된 에러 (Layer 1):
{errors_json}

### 검출된 이상치 (Layer 2):
{anomalies_json}

### 요구사항:
1. 사용자에게 물어볼 명확한 질문만 생성
2. 같은 패턴이 여러 개 있으면 배치 질문으로 통합
3. JSON 형식으로만 응답

### 응답 형식 (JSON):
{{
    "questions": [
        {{
            "id": "q1",
            "row": 2,
            "question": "행 2의 부서가 '영여'로 보이는데, '영업'인가요?",
            "suggested_fix": "영업",
            "confidence": 0.85
        }}
    ],
    "batch_groups": [
        {{
            "pattern": "영여 → 영업",
            "rows": [2, 7, 12],
            "count": 3,
            "question": "같은 오타 3개 발견. 모두 수정할까요?"
        }}
    ]
}}
"""
    return prompt



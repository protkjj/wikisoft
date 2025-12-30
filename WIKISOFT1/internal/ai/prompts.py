"""
AI Prompts for Normalization and Validation

모든 정규화와 검증을 한 번에 처리하는 프롬프트
"""

NORMALIZE_AND_VALIDATE_PROMPT = """
당신은 한국 HR 데이터 전문가입니다.

다음 직원 데이터를 정규화하고 오류를 찾아주세요:

[데이터]
{data_table}

[컬럼 설명]
{column_descriptions}

[정규화 규칙]
1. 전화번호: 01012345678 형식 (숫자만)
   예: "+82-10-1234-5678" → "01012345678"
   예: "010-1234-5678" → "01012345678"

2. 생년월일: YYYY-MM-DD 형식
   예: "2016.01.22" → "2016-01-22"
   예: "16/01/22" → "2016-01-22"
   예: "160122" → "2016-01-22"

3. 급여: 숫자만 (만원 단위)
   예: "5억 1000만원" → "51000"
   예: "5000만원" → "5000"
   예: "5억" → "50000"

[검증 규칙]
- 생년월일은 1900-01-01 ~ 현재 사이
- 입사일은 생년월일보다 이후, 현재보다 이전
- 급여는 항상 > 0
- 이상값 감지 (극단값, 논리 오류 등)
- 데이터 일관성 체크

[응답 형식 (JSON)]
{{
  "normalized_rows": [
    {{
      "row": 1,
      "columns": {{
        "전화": "01012345678",
        "생년월일": "2016-01-22",
        "급여": "5000"
      }}
    }}
  ],
  "errors": [
    {{
      "row": 2,
      "column": "급여",
      "original_value": "0",
      "error": "급여가 0입니다",
      "severity": "error",
      "suggestion": "양수를 입력해주세요"
    }}
  ]
}}

부족한 정보는 null로 반환하세요.
"""


def get_normalize_validate_prompt(df, column_mapping: dict) -> str:
    """
    프롬프트를 실제 데이터로 채우기
    
    Args:
        df: DataFrame
        column_mapping: 컬럼 설명
    
    Returns:
        완성된 프롬프트
    """
    # TODO: 구현
    # 1. DataFrame을 테이블 형식으로 변환
    # 2. 컬럼 설명 포맷팅
    # 3. 프롬프트에 삽입
    
    data_table = df.head(10).to_markdown()  # 임시
    column_desc = "\n".join([f"- {k}: {v}" for k, v in column_mapping.items()])
    
    return NORMALIZE_AND_VALIDATE_PROMPT.format(
        data_table=data_table,
        column_descriptions=column_desc
    )

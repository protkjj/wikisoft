"""
표준 데이터 스키마 정의 (v2에서 이식)
"""
from typing import Dict, Any, List

STANDARD_SCHEMA: Dict[str, Dict[str, Any]] = {
    "사원번호": {
        "type": "string",
        "description": "직원을 고유하게 식별하는 번호 또는 코드",
        "aliases": ["직원번호", "사번", "employee_id", "emp_no", "emp_id", "staff_no", "사원코드"],
        "examples": ["A001", "20230001", "EMP-123", "S-2024-001"],
        "required": True,
        "sheet": "재직자",
    },
    "이름": {
        "type": "string",
        "description": "직원의 성명 (한글 또는 영문)",
        "aliases": ["성명", "name", "full_name", "employee_name", "직원명"],
        "examples": ["홍길동", "김철수", "John Doe"],
        "required": True,
        "sheet": "재직자",
    },
    "생년월일": {
        "type": "date",
        "description": "직원의 출생일자",
        "aliases": ["출생일", "생일", "birth_date", "DOB", "date_of_birth", "Birthday"],
        "examples": ["1990-01-01", "19900101", "1990/01/01"],
        "required": True,
        "sheet": "재직자",
    },
    "성별": {
        "type": "category",
        "description": "성별 (남/여, M/F, 1/2 등)",
        "aliases": ["gender", "sex", "성별코드"],
        "examples": ["남", "여", "M", "F", "1", "2"],
        "required": True,
        "sheet": "재직자",
    },
    "입사일자": {
        "type": "date",
        "description": "회사에 입사한 날짜",
        "aliases": ["입사일", "입사년월일", "채용일", "hire_date", "join_date", "employment_date", "들어온날짜", "입사날짜"],
        "examples": ["2020-03-15", "20200315", "2020/03/15"],
        "required": True,
        "sheet": "재직자",
    },
    "종업원구분": {
        "type": "category",
        "description": "직원 유형 구분 (임원/직원/계약직 등)",
        "aliases": ["직원구분", "근로자구분", "employee_type", "emp_type", "직급구분", "고용형태"],
        "examples": ["1", "2", "3", "임원", "직원", "계약직"],
        "required": True,
        "sheet": "재직자",
    },
    "기준급여": {
        "type": "number",
        "description": "퇴직금 계산 기준이 되는 급여 (월 단위)",
        "aliases": ["급여", "월급", "salary", "기본급", "평균급여", "월평균급여"],
        "examples": ["5000000", "5,000,000", "500만원"],
        "required": True,
        "sheet": "재직자",
    },
    "부서": {
        "type": "string",
        "description": "소속 부서명",
        "aliases": ["부서명", "department", "dept", "소속부서", "팀"],
        "examples": ["영업부", "인사팀", "IT부문"],
        "required": False,
        "sheet": "재직자",
    },
    "직급": {
        "type": "string",
        "description": "직급 또는 직책",
        "aliases": ["직책", "position", "title", "rank", "직위"],
        "examples": ["사원", "대리", "과장", "부장", "이사"],
        "required": False,
        "sheet": "재직자",
    },
    "전화번호": {
        "type": "string",
        "description": "휴대폰 번호 또는 연락처",
        "aliases": ["휴대폰", "핸드폰", "전화", "phone", "mobile", "contact", "연락처"],
        "examples": ["01012345678", "010-1234-5678", "010 1234 5678"],
        "required": False,
        "sheet": "재직자",
    },
    "이메일": {
        "type": "string",
        "description": "이메일 주소",
        "aliases": ["email", "e-mail", "메일", "메일주소"],
        "examples": ["hong@company.com", "kim@example.co.kr"],
        "required": False,
        "sheet": "재직자",
    },
    "제도구분": {
        "type": "category",
        "description": "퇴직금 제도 구분 (DB/DC/혼합 등)",
        "aliases": ["퇴직제도", "연금제도", "pension_type"],
        "examples": ["1", "2", "3", "DB", "DC"],
        "required": False,
        "sheet": "재직자",
    },
    "적용배수": {
        "type": "number",
        "description": "퇴직금 계산 시 적용되는 배수",
        "aliases": ["배수", "multiplier", "계산배수"],
        "examples": ["1", "1.5", "2"],
        "required": False,
        "sheet": "재직자",
    },
    "당년도퇴직금추계액": {
        "type": "number",
        "description": "현재 연도 기준 예상 퇴직금 금액",
        "aliases": ["퇴직금추계액", "퇴직금예상액", "퇴직금", "estimated_retirement"],
        "examples": ["10000000", "1000만원"],
        "required": False,
        "sheet": "재직자",
    },
    "차년도퇴직금추계액": {
        "type": "number",
        "description": "다음 연도 기준 예상 퇴직금 금액",
        "aliases": ["내년퇴직금", "차년도퇴직금"],
        "examples": ["11000000"],
        "required": False,
        "sheet": "재직자",
    },
    "퇴직일": {
        "type": "date",
        "description": "퇴직한 날짜 또는 DC 전환일",
        "aliases": ["퇴사일", "퇴직일자", "DC전환일", "퇴직/전환일", "resignation_date", "retire_date"],
        "examples": ["2024-12-31", "20241231"],
        "required": False,
        "sheet": "퇴직자",
    },
    "사유": {
        "type": "category",
        "description": "퇴직 사유 (퇴직금정산/중간정산/DC전환 등)",
        "aliases": ["퇴직사유", "사유코드", "reason"],
        "examples": ["퇴직금정산", "중간정산", "DC전환", "관계사전출"],
        "required": False,
        "sheet": "퇴직자",
    },
    "퇴직금": {
        "type": "number",
        "description": "실제 지급된 퇴직금 또는 DC 전환금",
        "aliases": ["퇴직금액", "DC전환금", "퇴직/전환금", "severance_pay"],
        "examples": ["50000000", "5000만원"],
        "required": False,
        "sheet": "퇴직자",
    },
    "관계사명": {
        "type": "string",
        "description": "전입/전출 관계사 회사명",
        "aliases": ["전입사", "전출사", "관련회사"],
        "examples": ["(주)계열사", "A그룹"],
        "required": False,
        "sheet": "추가",
    },
    "전입전출금액": {
        "type": "number",
        "description": "관계사 전입/전출 금액",
        "aliases": ["전입금액", "전출금액", "이동금액"],
        "examples": ["30000000"],
        "required": False,
        "sheet": "추가",
    },
}


def get_required_fields(sheet_type: str = "재직자") -> List[str]:
    return [
        name
        for name, schema in STANDARD_SCHEMA.items()
        if schema.get("required") and schema.get("sheet") == sheet_type
    ]


def get_all_aliases(field_name: str) -> List[str]:
    schema = STANDARD_SCHEMA.get(field_name)
    if not schema:
        return []
    return [field_name] + schema.get("aliases", [])


def find_field_by_alias(alias: str) -> str:
    alias_lower = alias.lower().strip()
    for field_name, schema in STANDARD_SCHEMA.items():
        if field_name.lower() == alias_lower:
            return field_name
        for a in schema.get("aliases", []):
            if a.lower() == alias_lower:
                return field_name
    return None

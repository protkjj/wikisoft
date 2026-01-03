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
        "required": False,  # 개인정보 보호 - 명부에 이름 제외 가능
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
        "aliases": ["gender", "sex", "성별코드", "성별 (1:남자, 2:여자)", "성별(1:남,2:여)"],
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
        "aliases": [
            # 종업원 관련
            "종업원 구분", "종업원구분", "종업원유형", "종업원 유형",
            "종업원 구분 (1:직원, 3:임원, 4:계약직)", "종업원구분 (1:직원, 3:임원, 4:계약직)",
            # 직종 관련
            "직종구분", "직종 구분", "직종구분 (1,2:직원, 3:임원, 4:계약직)",
            # 직원/근로자 관련
            "직원구분", "직원 구분", "근로자구분", "근로자 구분",
            # 고용 관련
            "고용형태", "고용 형태", "고용유형", "고용 유형",
            # 직급 관련
            "직급구분", "직급 구분",
            # 영문
            "employee_type", "emp_type", "employment_type"
        ],
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
        "aliases": ["퇴직금추계액", "퇴직금예상액", "퇴직금", "estimated_retirement", "당년도 퇴직금추계액"],
        "examples": ["10000000", "1000만원"],
        "required": False,
        "sheet": "재직자",
    },
    "차년도퇴직금추계액": {
        "type": "number",
        "description": "다음 연도 기준 예상 퇴직금 금액",
        "aliases": ["내년퇴직금", "차년도퇴직금", "차년도 퇴직금추계액"],
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
    # ===== 실제 고객 데이터에서 자주 등장하는 추가 필드들 =====
    "중간정산기준일": {
        "type": "date",
        "description": "중간정산 기준일",
        "aliases": ["중간정산일", "정산기준일"],
        "examples": ["2020-12-31", "20201231"],
        "required": False,
        "sheet": "재직자",
    },
    "중간정산액": {
        "type": "number",
        "description": "중간정산 금액",
        "aliases": ["정산액", "중간정산금액"],
        "examples": ["10000000"],
        "required": False,
        "sheet": "재직자",
    },
    "적용제도번호": {
        "type": "string",
        "description": "적용되는 퇴직금 제도 번호",
        "aliases": ["제도번호", "적용제도"],
        "examples": ["1", "2", "001"],
        "required": False,
        "sheet": "재직자",
    },
    "추가CODE1": {
        "type": "string",
        "description": "고객사 정의 추가 코드 1",
        "aliases": ["추가코드1", "CODE1", "부가코드1", "추가code1"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE2": {
        "type": "string",
        "description": "고객사 정의 추가 코드 2",
        "aliases": ["추가코드2", "CODE2", "부가코드2", "추가code2"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE3": {
        "type": "string",
        "description": "고객사 정의 추가 코드 3",
        "aliases": ["추가코드3", "CODE3", "부가코드3", "추가code3"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE4": {
        "type": "string",
        "description": "고객사 정의 추가 코드 4",
        "aliases": ["추가코드4", "CODE4", "부가코드4", "추가code4"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE5": {
        "type": "string",
        "description": "고객사 정의 추가 코드 5",
        "aliases": ["추가코드5", "CODE5", "부가코드5", "추가code5"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE6": {
        "type": "string",
        "description": "고객사 정의 추가 코드 6",
        "aliases": ["추가코드6", "CODE6", "부가코드6", "추가code6"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE7": {
        "type": "string",
        "description": "고객사 정의 추가 코드 7",
        "aliases": ["추가코드7", "CODE7", "부가코드7", "추가code7"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE8": {
        "type": "string",
        "description": "고객사 정의 추가 코드 8",
        "aliases": ["추가코드8", "CODE8", "부가코드8", "추가code8"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE9": {
        "type": "string",
        "description": "고객사 정의 추가 코드 9",
        "aliases": ["추가코드9", "CODE9", "부가코드9", "추가code9"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CODE10": {
        "type": "string",
        "description": "고객사 정의 추가 코드 10",
        "aliases": ["추가코드10", "CODE10", "부가코드10", "추가code10"],
        "examples": ["A", "B", "001"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR1": {
        "type": "string",
        "description": "고객사 정의 추가 문자 1 (예: 가입여부)",
        "aliases": ["추가CHAR1 (가입여부 Y/N)", "가입여부"],
        "examples": ["Y", "N"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR2": {
        "type": "string",
        "description": "고객사 정의 추가 문자 2 (예: 축소/청산 구분)",
        "aliases": ["추가CHAR2 (1:축소, 2:청산, 3:사업결합, 4:청산_중간정산)"],
        "examples": ["1", "2", "3", "4"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR3": {
        "type": "string",
        "description": "고객사 정의 추가 문자 3",
        "aliases": ["추가문자3"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR4": {
        "type": "string",
        "description": "고객사 정의 추가 문자 4",
        "aliases": ["추가문자4"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR5": {
        "type": "string",
        "description": "고객사 정의 추가 문자 5",
        "aliases": ["추가문자5"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR6": {
        "type": "string",
        "description": "고객사 정의 추가 문자 6",
        "aliases": ["추가문자6"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR7": {
        "type": "string",
        "description": "고객사 정의 추가 문자 7",
        "aliases": ["추가문자7"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR8": {
        "type": "string",
        "description": "고객사 정의 추가 문자 8",
        "aliases": ["추가문자8"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR9": {
        "type": "string",
        "description": "고객사 정의 추가 문자 9",
        "aliases": ["추가문자9"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가CHAR10": {
        "type": "string",
        "description": "고객사 정의 추가 문자 10",
        "aliases": ["추가문자10"],
        "examples": ["A", "B"],
        "required": False,
        "sheet": "추가",
    },
    "추가NUMBER1": {
        "type": "number",
        "description": "고객사 정의 추가 숫자 1 (예: 추가지급률)",
        "aliases": ["추가NUMBER1 추가지급률", "추가지급률"],
        "examples": ["0.1", "0.05"],
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

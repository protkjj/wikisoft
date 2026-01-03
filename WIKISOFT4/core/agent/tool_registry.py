"""
Tool Registry: 파서/매칭/검증/리포트 도구를 중앙에서 관리
"""
from typing import Any, Callable, Dict, List
import re

from core.ai.matcher import match_headers
from core.ai.knowledge_base import add_error_rule, learn_from_correction
from core.generators.report import generate_report
from core.parsers.parser import parse_roster
from core.validators.validator import validate
from core.validators.duplicate_detector import detect_duplicates


# ========================================
# 개인정보 마스킹 유틸리티
# ========================================

def mask_personal_info(text: str) -> str:
    """개인정보 마스킹 (생년월일, 사원번호 등)"""
    result = text
    
    # 날짜 마스킹: YYYY-MM-DD → YYYY-**-**
    result = re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\1-**-**', result)
    # YYYYMMDD → YYYY****
    result = re.sub(r'(\d{4})(\d{4})(?!\d)', r'\1****', result)
    # 사원번호 패턴 (4자리 이상 숫자) → 앞 2자리만
    # result = re.sub(r'(\d{2})\d{4,}', r'\1****', result)
    
    return result


# ========================================
# 검증용 도구 함수들 (AI가 호출)
# ========================================

def compare_headcount(reported: int, actual: int) -> Dict[str, Any]:
    """진단 응답 인원수와 실제 명부 인원수 비교"""
    if reported == actual:
        return {"match": True, "message": f"인원수 일치: {actual}명"}
    else:
        diff = actual - reported
        return {
            "match": False, 
            "message": f"인원수 불일치: 진단 {reported}명, 실제 {actual}명 (차이: {diff:+d}명)",
            "severity": "warning"
        }

def check_date_order(birth_date: str, hire_date: str, emp_id: str = None) -> Dict[str, Any]:
    """생년월일과 입사일 순서 확인"""
    from core.utils.date_utils import normalize_date
    import pandas as pd
    
    birth_norm = normalize_date(birth_date)
    hire_norm = normalize_date(hire_date)
    
    if not birth_norm or not hire_norm:
        return {"valid": None, "message": "날짜 파싱 불가"}
    
    birth_dt = pd.to_datetime(birth_norm, format="%Y%m%d", errors="coerce")
    hire_dt = pd.to_datetime(hire_norm, format="%Y%m%d", errors="coerce")
    
    if pd.isnull(birth_dt) or pd.isnull(hire_dt):
        return {"valid": None, "message": "날짜 변환 불가"}
    
    if hire_dt < birth_dt:
        emp_info = f" (사원 {emp_id[:4]}****)" if emp_id else ""
        return {
            "valid": False, 
            "message": f"입사일이 생년월일보다 앞섬{emp_info}",
            "severity": "error"
        }
    
    age_at_hire = (hire_dt - birth_dt).days / 365.25
    if age_at_hire < 18:
        return {"valid": False, "message": f"입사 나이 {int(age_at_hire)}세 (18세 미만)", "severity": "error"}
    elif age_at_hire > 70:
        return {"valid": True, "message": f"입사 나이 {int(age_at_hire)}세 (70세 초과, 확인 필요)", "severity": "question"}
    
    return {"valid": True, "message": f"정상 (입사 나이 {int(age_at_hire)}세)"}

def find_duplicate_emp_ids(rows: List[Dict], emp_id_col: str = "사원번호") -> Dict[str, Any]:
    """중복 사원번호 찾기"""
    emp_ids = [str(row.get(emp_id_col, "")).strip() for row in rows if row.get(emp_id_col)]
    seen = {}
    duplicates = []
    
    for idx, emp_id in enumerate(emp_ids):
        if emp_id in seen:
            if emp_id not in [d["emp_id"] for d in duplicates]:
                duplicates.append({"emp_id": emp_id, "rows": [seen[emp_id], idx + 1]})
            else:
                for d in duplicates:
                    if d["emp_id"] == emp_id:
                        d["rows"].append(idx + 1)
        else:
            seen[emp_id] = idx + 1
    
    if duplicates:
        return {
            "has_duplicates": True,
            "count": len(duplicates),
            "duplicates": duplicates[:5],  # 최대 5개만
            "message": f"중복 사원번호 {len(duplicates)}건 발견",
            "severity": "warning"
        }
    return {"has_duplicates": False, "message": "중복 사원번호 없음"}

def check_required_fields(row: Dict, required: List[str]) -> Dict[str, Any]:
    """필수 필드 존재 여부 확인"""
    import pandas as pd
    missing = []
    for field in required:
        val = row.get(field)
        if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
            missing.append(field)
    
    if missing:
        return {"complete": False, "missing": missing, "message": f"필수 필드 누락: {', '.join(missing)}"}
    return {"complete": True, "message": "모든 필수 필드 존재"}

def count_empty_rows(rows: List[Dict], required_cols: List[str]) -> Dict[str, Any]:
    """빈 행 개수 세기"""
    import pandas as pd
    empty_count = 0
    empty_rows = []
    
    for idx, row in enumerate(rows):
        all_empty = True
        for col in required_cols:
            val = row.get(col)
            if val is not None and not (isinstance(val, float) and pd.isna(val)) and str(val).strip():
                all_empty = False
                break
        if all_empty:
            empty_count += 1
            if len(empty_rows) < 5:
                empty_rows.append(idx + 1)
    
    if empty_count > 0:
        return {"has_empty": True, "count": empty_count, "rows": empty_rows, "message": f"빈 행 {empty_count}개 발견"}
    return {"has_empty": False, "message": "빈 행 없음"}


class ToolRegistry:
    """Tool 레지스트리: Agent가 호출 가능한 도구들을 관리."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {
            # 기존 도구들
            "parse_roster": {
                "func": parse_roster,
                "description": "Excel/CSV 파일 파싱",
                "params": ["file_bytes", "sheet_name", "max_rows"],
            },
            "match_headers": {
                "func": match_headers,
                "description": "고객 헤더를 표준 스키마에 매칭",
                "params": ["parsed", "sheet_type"],
            },
            "validate": {
                "func": validate,
                "description": "파싱/매칭 결과 유효성 검사 (L1/L2)",
                "params": ["parsed", "matches"],
            },
            "generate_report": {
                "func": generate_report,
                "description": "검증 결과 리포트 생성",
                "params": ["validation"],
            },
            "detect_duplicates": {
                "func": detect_duplicates,
                "description": "중복 행 탐지 (완전/유사/의심)",
                "params": ["df", "headers", "matches"],
            },
            "add_error_rule": {
                "func": add_error_rule,
                "description": "새로운 오류 검증 규칙 학습",
                "params": ["field", "condition", "message", "severity", "category"],
            },
            "learn_from_correction": {
                "func": learn_from_correction,
                "description": "사용자 수정에서 패턴 학습",
                "params": ["field", "original_value", "was_error", "correct_interpretation", "diagnostic_context"],
            },
            # 검증용 도구들 (AI Agent가 호출)
            "compare_headcount": {
                "func": compare_headcount,
                "description": "진단 응답 인원수와 실제 명부 인원수 비교. 같으면 일치, 다르면 불일치 반환.",
                "params": ["reported", "actual"],
            },
            "check_date_order": {
                "func": check_date_order,
                "description": "생년월일과 입사일 순서 확인. 입사일이 생년월일보다 앞서면 오류.",
                "params": ["birth_date", "hire_date", "emp_id"],
            },
            "find_duplicate_emp_ids": {
                "func": find_duplicate_emp_ids,
                "description": "중복 사원번호 찾기. 동일한 사원번호가 여러 행에 있으면 반환.",
                "params": ["rows", "emp_id_col"],
            },
            "check_required_fields": {
                "func": check_required_fields,
                "description": "특정 행에 필수 필드가 모두 있는지 확인.",
                "params": ["row", "required"],
            },
            "count_empty_rows": {
                "func": count_empty_rows,
                "description": "필수 컬럼이 모두 비어있는 빈 행 개수 세기.",
                "params": ["rows", "required_cols"],
            },
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [{"name": name, "description": info["description"], "params": info["params"]} for name, info in self.tools.items()]

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        func = self.tools[tool_name]["func"]
        return func(**kwargs)

    def get_tool(self, tool_name: str) -> Callable:
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        return self.tools[tool_name]["func"]


# 글로벌 레지스트리
_registry = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

"""
WIKISOFT3 IFRS 1019 퇴직급여 부채 계산 스크립트
Windmill에서 Python 스크립트로 사용

검증 완료된 데이터로 IFRS 계산 수행
"""

import os
import requests
from typing import TypedDict, Optional, Any, List

# 기본 API URL (환경변수로 오버라이드 가능)
DEFAULT_API_URL = os.getenv("WIKISOFT_API_URL", "http://localhost:8003")


class IFRSResult(TypedDict):
    success: bool
    summary: Optional[dict]  # total_dbo, total_csc, total_interest_cost
    employees: Optional[List[dict]]  # 개인별 계산 결과
    assumptions: Optional[dict]  # 적용된 가정
    error: Optional[str]


def main(
    headers: List[str],
    rows: List[List[Any]],
    matches: List[dict],
    api_url: str = None,
    discount_rate: float = 0.045,
    salary_increase_rate: float = 0.03,
    turnover_rate: float = 0.05,
    retirement_age: int = 60
) -> IFRSResult:
    """
    검증된 명부 데이터로 IFRS 1019 퇴직급여 부채를 계산합니다.

    Args:
        headers: 헤더 리스트 (validate_roster 결과에서 전달)
        rows: 데이터 행 리스트
        matches: 헤더 매칭 결과
        api_url: WIKISOFT3 API 서버 URL
        discount_rate: 할인율 (기본 4.5%)
        salary_increase_rate: 임금상승률 (기본 3%)
        turnover_rate: 이직률 (기본 5%)
        retirement_age: 정년 (기본 60세)

    Returns:
        IFRSResult:
            - success: 성공 여부
            - summary: 전체 합계 (total_dbo, total_csc, total_interest_cost)
            - employees: 개인별 계산 결과
            - assumptions: 적용된 가정

    Example (Windmill Flow에서):
        # Step 1: 검증
        validation = validate_roster.main(file_url="...")

        if validation["action"] == "auto_approve":
            # Step 2: IFRS 계산
            ifrs = ifrs_calculate.main(
                headers=validation["parsed"]["headers"],
                rows=validation["parsed"]["rows"],
                matches=validation["matches"]["matches"]
            )
    """
    # 환경변수 또는 기본값 사용
    api_url = api_url or DEFAULT_API_URL

    try:
        response = requests.post(
            f"{api_url}/api/tools/ifrs-calculate",
            json={
                "headers": headers,
                "rows": rows,
                "matches": matches,
                "assumptions": {
                    "discount_rate": discount_rate,
                    "salary_increase_rate": salary_increase_rate,
                    "turnover_rate": turnover_rate,
                    "retirement_age": retirement_age
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            data = result.get("result", {})
            return IFRSResult(
                success=True,
                summary=data.get("summary"),
                employees=data.get("employees"),
                assumptions=data.get("assumptions"),
                error=None
            )
        else:
            return IFRSResult(
                success=False,
                summary=None,
                employees=None,
                assumptions=None,
                error=result.get("error", "알 수 없는 오류")
            )

    except Exception as e:
        return IFRSResult(
            success=False,
            summary=None,
            employees=None,
            assumptions=None,
            error=str(e)
        )

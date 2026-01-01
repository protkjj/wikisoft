"""
WIKISOFT3 재직자명부 검증 스크립트
Windmill에서 Python 스크립트로 사용

사용법:
1. Windmill에서 새 Script 생성
2. 이 코드 복사/붙여넣기
3. WIKISOFT3_API_URL 환경변수 설정 (예: https://your-ngrok-url.ngrok.io)
"""

import os
import requests
from typing import TypedDict, Optional, Any

# 기본 API URL (환경변수로 오버라이드 가능)
DEFAULT_API_URL = os.getenv("WIKISOFT_API_URL", "http://localhost:8003")


class ValidationResult(TypedDict):
    success: bool
    action: str  # "auto_approve" | "needs_review" | "rejected"
    auto_approve: bool
    confidence: float
    message: str
    parsed: Optional[dict]
    matches: Optional[dict]
    validation: Optional[dict]
    errors: Optional[list]
    warnings: Optional[list]


def main(
    file_url: str,
    sheet_type: str = "재직자",
    api_url: str = None,
    auto_approve_threshold: float = 0.90
) -> ValidationResult:
    """
    재직자명부 파일을 검증하고 분기 결정을 반환합니다.

    Args:
        file_url: 검증할 Excel 파일 URL (S3, Google Drive 등)
        sheet_type: 시트 유형 ("재직자" 또는 "퇴직자")
        api_url: WIKISOFT3 API 서버 URL
        auto_approve_threshold: 자동 승인 신뢰도 기준 (기본 0.90)

    Returns:
        ValidationResult: 검증 결과
            - action: "auto_approve" | "needs_review" | "rejected"
            - auto_approve: 자동 승인 가능 여부
            - confidence: 신뢰도 점수 (0-1)
            - message: 결과 메시지

    Example:
        result = main(
            file_url="https://example.com/roster.xlsx",
            sheet_type="재직자",
            api_url="https://xxxx.ngrok.io"
        )

        if result["action"] == "auto_approve":
            # 자동 승인 → IFRS 계산 진행
            pass
        elif result["action"] == "needs_review":
            # 수동 검토 필요 → 담당자 알림
            pass
        else:  # rejected
            # 파일 반려 → 재업로드 요청
            pass
    """
    # 환경변수 또는 기본값 사용
    api_url = api_url or DEFAULT_API_URL

    # 1. 파일 다운로드
    try:
        file_response = requests.get(file_url, timeout=30)
        file_response.raise_for_status()
        file_bytes = file_response.content

        # 파일명 추출
        filename = file_url.split("/")[-1].split("?")[0]
        if not filename.endswith((".xls", ".xlsx")):
            filename = "roster.xlsx"

    except Exception as e:
        return ValidationResult(
            success=False,
            action="rejected",
            auto_approve=False,
            confidence=0.0,
            message=f"파일 다운로드 실패: {str(e)}",
            parsed=None,
            matches=None,
            validation=None,
            errors=[{"type": "download_error", "message": str(e)}],
            warnings=None
        )

    # 2. WIKISOFT3 API 호출
    try:
        response = requests.post(
            f"{api_url}/api/windmill/trigger",
            files={"file": (filename, file_bytes)},
            data={
                "sheet_type": sheet_type,
                "auto_approve_threshold": str(auto_approve_threshold)
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        return ValidationResult(
            success=result.get("success", False),
            action=result.get("action", "rejected"),
            auto_approve=result.get("auto_approve", False),
            confidence=result.get("confidence", 0.0),
            message=result.get("message", ""),
            parsed=result.get("parsed"),
            matches=result.get("matches"),
            validation=result.get("validation"),
            errors=result.get("errors"),
            warnings=result.get("warnings")
        )

    except requests.exceptions.Timeout:
        return ValidationResult(
            success=False,
            action="rejected",
            auto_approve=False,
            confidence=0.0,
            message="API 요청 시간 초과",
            parsed=None,
            matches=None,
            validation=None,
            errors=[{"type": "timeout_error", "message": "API 응답 시간 초과 (60초)"}],
            warnings=None
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            action="rejected",
            auto_approve=False,
            confidence=0.0,
            message=f"API 호출 실패: {str(e)}",
            parsed=None,
            matches=None,
            validation=None,
            errors=[{"type": "api_error", "message": str(e)}],
            warnings=None
        )

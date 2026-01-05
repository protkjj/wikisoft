"""
리포트 생성 API

검증 결과를 Excel 리포트로 생성
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.generators import generate_excel_report, generate_final_data_excel


router = APIRouter(prefix="/report", tags=["Report"])


class ValidationReportRequest(BaseModel):
    """검증 결과 리포트 요청"""
    validation_result: Dict[str, Any] = Field(..., description="검증 결과 데이터")
    original_data: Optional[Dict[str, Any]] = Field(None, description="원본 파싱 데이터")
    answers: Optional[Dict[str, Any]] = Field(None, description="진단 답변")
    filename: Optional[str] = Field("validation_report", description="출력 파일명")


@router.post("/validation")
async def generate_validation_report(request: ValidationReportRequest):
    """
    검증 결과 리포트 생성 (Excel)

    - 요약 시트: 검증 상태, 신뢰도
    - 매칭 결과 시트: 헤더 매핑 정보
    - 이상 탐지 시트: 발견된 이상 항목
    - 원본 데이터 시트: 하이라이팅 포함
    """
    try:
        excel_bytes = generate_excel_report(
            request.validation_result,
            request.original_data,
            request.answers
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{request.filename}_{timestamp}.xlsx"

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(output_filename)}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")


@router.post("/final-data")
async def generate_final_data_report(
    original_data: Dict[str, Any],
    validation_result: Dict[str, Any],
    filename: str = "final_data"
):
    """
    최종 수정본 Excel 생성

    매핑 완료된 깔끔한 데이터 (표준 필드명 적용)
    """
    try:
        excel_bytes = generate_final_data_excel(original_data, validation_result)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{filename}_{timestamp}.xlsx"

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(output_filename)}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {str(e)}")

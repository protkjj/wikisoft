from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from io import BytesIO

from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.agent.tool_registry import get_registry
from internal.generators.report import generate_excel_report

router = APIRouter(prefix="/auto-validate", tags=["auto-validate"])

# 임시 저장소 (실제 서비스에서는 Redis/DB 사용)
_last_validation_result = {}
_last_parsed_data = {}


@router.post("")
async def auto_validate(file: UploadFile = File(...)) -> dict:
    """파일 업로드 → 파싱 → 매칭 → 검증 → 리포트 파이프라인."""
    global _last_validation_result, _last_parsed_data
    
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is required")

    file_bytes = await file.read()
    registry = get_registry()

    # 1. 파싱
    parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)

    # 2. 헤더 매칭
    matches = registry.call_tool("match_headers", parsed=parsed, sheet_type="재직자")

    # 3. 검증
    validation = registry.call_tool("validate", parsed=parsed, matches=matches)

    # 4. 신뢰도/이상치 분석
    confidence = estimate_confidence(parsed, matches, validation)
    anomalies = detect_anomalies(parsed, matches, validation)

    # 5. 리포트 생성
    report = registry.call_tool("generate_report", validation=validation)

    result = {
        "status": "ok",
        "confidence": confidence,
        "anomalies": anomalies,
        "steps": {
            "parsed_summary": {
                "headers": parsed.get("headers", []),
                "row_count": len(parsed.get("rows", [])),
            },
            "matches": matches,
            "validation": validation,
            "report": report,
        },
    }
    
    # 결과 저장 (Excel 다운로드용)
    _last_validation_result = result
    _last_parsed_data = parsed
    
    return result


@router.get("/download-excel")
async def download_excel():
    """마지막 검증 결과를 Excel 파일로 다운로드"""
    global _last_validation_result, _last_parsed_data
    
    if not _last_validation_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="검증 결과가 없습니다. 먼저 파일을 검증해주세요."
        )
    
    try:
        excel_bytes = generate_excel_report(
            validation_result=_last_validation_result,
            original_data=_last_parsed_data
        )
        
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=validation_result.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel 생성 오류: {str(e)}"
        )

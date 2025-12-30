from fastapi import APIRouter, File, HTTPException, UploadFile, status

from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.agent.tool_registry import get_registry

router = APIRouter(prefix="/auto-validate", tags=["auto-validate"])


@router.post("")
async def auto_validate(file: UploadFile = File(...)) -> dict:
    """파일 업로드 → 파싱 → 매칭 → 검증 → 리포트 파이프라인."""
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

    return {
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

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import Optional
import json

from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.agent.tool_registry import get_registry
from internal.generators.report import generate_excel_report

router = APIRouter(prefix="/auto-validate", tags=["auto-validate"])

# 임시 저장소 (실제 서비스에서는 Redis/DB 사용)
_last_validation_result = {}
_last_parsed_data = {}
_last_diagnostic_answers = {}


@router.post("")
async def auto_validate(
    file: UploadFile = File(...),
    chatbot_answers: Optional[str] = Form(None)
) -> dict:
    """파일 업로드 → 파싱 → 매칭 → 검증 → 리포트 파이프라인.
    
    chatbot_answers: 진단 질문 답변 (JSON 문자열)
    - 예/아니오 답변을 기반으로 검증 규칙 조정
    """
    global _last_validation_result, _last_parsed_data, _last_diagnostic_answers
    
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is required")

    # 진단 답변 파싱
    diagnostic_answers = {}
    if chatbot_answers:
        try:
            diagnostic_answers = json.loads(chatbot_answers)
            _last_diagnostic_answers = diagnostic_answers
        except json.JSONDecodeError:
            pass

    file_bytes = await file.read()
    registry = get_registry()

    # 1. 파싱
    parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)

    # 2. 헤더 매칭
    matches = registry.call_tool("match_headers", parsed=parsed, sheet_type="재직자")

    # 3. 검증 (진단 답변 전달)
    validation = registry.call_tool("validate", parsed=parsed, matches=matches, diagnostic_answers=diagnostic_answers)

    # 4. 신뢰도/이상치 분석
    confidence = estimate_confidence(parsed, matches, validation)
    anomalies = detect_anomalies(parsed, matches, validation)
    
    # 5. 진단 답변 기반 추가 검증/경고
    diagnostic_warnings = check_diagnostic_consistency(parsed, diagnostic_answers)
    if diagnostic_warnings:
        anomalies["anomalies"].extend(diagnostic_warnings)

    # 6. 리포트 생성
    report = registry.call_tool("generate_report", validation=validation)

    result = {
        "status": "ok",
        "confidence": confidence,
        "anomalies": anomalies,
        "diagnostic_applied": bool(diagnostic_answers),
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


def check_diagnostic_consistency(parsed: dict, answers: dict) -> list:
    """진단 질문 답변과 실제 데이터 간 불일치 검사
    
    - 기본 규칙: 코드로 체크 (정말 단순한 것만 - 인원수 합계)
    - 나머지 전부: AI가 자유롭게 판단
    """
    if not answers:
        return []
    
    warnings = []
    rows = parsed.get("rows", [])
    headers = parsed.get("headers", [])
    row_count = len(rows)
    
    # ========================================
    # 1. 정말 기본적인 것만 코드로 (숫자 비교)
    # ========================================
    
    # 인원수 합계 vs 실제 행 수 비교
    headcount_questions = ["q19", "q20", "q21", "q22", "q23"]
    total_reported = sum(
        int(answers.get(q, 0)) 
        for q in headcount_questions 
        if str(answers.get(q, "")).isdigit()
    )
    
    if total_reported > 0 and abs(row_count - total_reported) > 0:
        warnings.append({
            "type": "headcount_mismatch",
            "severity": "warning",
            "message": f"인원수 불일치: 진단 답변 합계 {total_reported}명, 실제 명부 {row_count}명"
        })
    
    # ========================================
    # 2. 나머지는 AI Agent가 자유롭게 판단
    # ========================================
    try:
        ai_result = _ai_agent_analyze(parsed, answers, row_count, headers, rows)
        warnings.extend(ai_result.get("issues", []))
        
        # AI가 고객에게 물어볼 질문이 있으면 추가
        if ai_result.get("questions_for_customer"):
            for q in ai_result["questions_for_customer"]:
                warnings.append({
                    "type": "ai_question",
                    "severity": "question",
                    "message": q
                })
    except Exception as e:
        print(f"AI Agent 분석 실패: {e}")
    
    return warnings


def _ai_agent_analyze(parsed: dict, answers: dict, row_count: int, headers: list, rows: list) -> dict:
    """
    AI Agent가 자유롭게 데이터를 분석하고 판단.
    - 문제 발견 시 이슈 생성
    - 자동 수정 가능하면 수정 제안
    - 확인 필요하면 고객에게 질문 생성
    """
    from internal.ai.llm_client import chat
    from internal.ai.knowledge_base import get_error_check_rules
    
    # 샘플 데이터 (처음 10행)
    sample_rows = rows[:10] if rows else []
    sample_data = []
    for row in sample_rows:
        if isinstance(row, dict):
            sample_data.append({k: str(v)[:50] for k, v in list(row.items())[:8]})
        elif isinstance(row, (list, tuple)):
            sample_data.append([str(v)[:50] for v in row[:8]])
    
    analysis_prompt = f"""당신은 퇴직급여채무 검증 AI 에이전트입니다.
아래 데이터를 자유롭게 분석하고, 문제가 있으면 지적하세요.

## 참고 규칙 (이미 알고 있는 것 + 추가 참고):
{get_error_check_rules()}

## 고객 진단 답변:
{_format_answers_for_ai(answers)}

## 명부 데이터:
- 총 직원: {row_count}명
- 컬럼: {headers}
- 샘플 데이터 (처음 10행): {sample_data}

## 당신의 역할:
1. **자유롭게 분석**: 위 규칙뿐 아니라, 데이터에서 이상한 점을 발견하면 지적
2. **자동 수정 제안**: 명확한 오류는 수정 방법 제안
3. **고객 질문 생성**: 확인이 필요한 것은 질문으로 만들어서 고객에게 물어봄

## 응답 형식 (JSON만):
{{
  "issues": [
    {{"severity": "error|warning|info", "message": "발견한 문제", "auto_fix": "수정 제안 (있으면)"}}
  ],
  "questions_for_customer": [
    "고객에게 확인이 필요한 질문 (있으면)"
  ],
  "summary": "전체 분석 요약 한 줄"
}}

JSON만 출력하세요."""

    response = chat(analysis_prompt)
    
    import json
    response_text = response.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    result = json.loads(response_text)
    return result if isinstance(result, dict) else {"issues": [], "questions_for_customer": []}


def _format_answers_for_ai(answers: dict) -> str:
    """진단 답변을 AI가 이해하기 쉬운 형태로 포맷팅"""
    question_labels = {
        "q1": "사외적립자산 일치 여부",
        "q2": "정년 (세)",
        "q3": "임금피크제 적용",
        "q4": "기타장기종업원급여",
        "q5": "급여체계 (연봉제/호봉제)",
        "q6": "해고 등급",
        "q7": "1년 미만 재직자 포함",
        "q8": "기준급여",
        "q9": "퇴직지급율",
        "q10": "월할계산",
        "q11": "할인율",
        "q12": "임금상승률",
        "q13": "중간정산 여부",
        "q19": "정규직 인원수",
        "q20": "임원 인원수",
        "q21": "1년 미만 재직자 수",
        "q22": "정년 초과자 수",
        "q23": "계약직 인원수",
    }
    
    lines = []
    for qid, value in answers.items():
        label = question_labels.get(qid, qid)
        lines.append(f"- {label}: {value}")
    
    return "\n".join(lines)


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

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import Optional
import json

from internal.agent.confidence import detect_anomalies, estimate_confidence
from internal.agent.tool_registry import get_registry
from internal.agent.react_agent import create_react_agent
from internal.ai.diagnostic_questions import format_answers_for_ai
from internal.generators.report import generate_excel_report, generate_final_data_excel
from internal.memory.case_store import save_successful_case
from internal.memory.session_store import session_store
from internal.utils.security import validate_upload_file, secure_logger

router = APIRouter(prefix="/auto-validate", tags=["auto-validate"])


@router.post("")
async def auto_validate(
    file: UploadFile = File(...),
    chatbot_answers: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(None)
) -> dict:
    """파일 업로드 → 파싱 → 매칭 → 검증 → 리포트 파이프라인.

    chatbot_answers: 진단 질문 답변 (JSON 문자열)
    x_session_id: 세션 ID (없으면 자동 생성)

    Returns:
        session_id를 포함한 검증 결과 (다운로드 시 필요)
    """
    # 세션 생성/조회
    session_id = session_store.get_or_create(x_session_id)

    # 파일 검증 (타입, 크기, 매직바이트)
    file_bytes, filename = await validate_upload_file(file)
    secure_logger.info(f"파일 업로드: {filename}, 크기: {len(file_bytes)} bytes, 세션: {session_id[:8]}...")

    # 진단 답변 파싱
    diagnostic_answers = {}
    if chatbot_answers:
        try:
            diagnostic_answers = json.loads(chatbot_answers)
            session_store.set(session_id, "diagnostic_answers", diagnostic_answers)
        except json.JSONDecodeError:
            pass

    registry = get_registry()

    # 1. 파싱
    parsed = registry.call_tool("parse_roster", file_bytes=file_bytes)

    # 2. 헤더 매칭
    matches = registry.call_tool("match_headers", parsed=parsed, sheet_type="재직자")
    
    # 무시 컬럼 필터링 (UI에 표시하지 않음)
    filtered_matches = [
        m for m in matches.get("matches", [])
        if not m.get("ignored", False)
    ]
    matches_for_response = {**matches, "matches": filtered_matches}

    # 3. 검증 (진단 답변 전달)
    validation = registry.call_tool("validate", parsed=parsed, matches=matches, diagnostic_answers=diagnostic_answers)

    # 4. 신뢰도/이상치 분석
    confidence = estimate_confidence(parsed, matches, validation)
    anomalies = detect_anomalies(parsed, matches, validation)
    
    # 매칭 경고 (필수 필드 누락 등)를 anomalies에 추가
    for warning in matches.get("warnings", []):
        anomalies["anomalies"].append({
            "type": "matching_warning",
            "severity": "warning",
            "message": warning
        })
        anomalies["detected"] = True

    # 5. 중복 탐지
    import pandas as pd
    df = pd.DataFrame(parsed.get("rows", []), columns=parsed.get("headers", []))
    duplicates = registry.call_tool(
        "detect_duplicates",
        df=df,
        headers=parsed.get("headers", []),
        matches=matches.get("matches", [])
    )

    # 중복을 anomalies에 추가
    if duplicates.get("has_duplicates"):
        for dup in duplicates.get("exact_duplicates", []):
            anomalies["anomalies"].append({
                "type": "duplicate",
                "severity": "error",
                "message": dup["message"]
            })
        for dup in duplicates.get("similar_duplicates", []):
            anomalies["anomalies"].append({
                "type": "duplicate",
                "severity": "warning",
                "message": dup["message"]
            })
        anomalies["detected"] = True

    # 6. 진단 답변 기반 추가 검증/경고
    diagnostic_warnings = check_diagnostic_consistency(parsed, diagnostic_answers)
    if diagnostic_warnings:
        anomalies["anomalies"].extend(diagnostic_warnings)

    # 7. 리포트 생성
    report = registry.call_tool("generate_report", validation=validation)
    
    # 8. 개인정보 마스킹 적용
    from internal.agent.tool_registry import mask_personal_info
    
    def mask_anomalies(anomalies_data):
        """anomalies 내 메시지에서 개인정보 마스킹"""
        if not anomalies_data:
            return anomalies_data
        masked = dict(anomalies_data)
        if "anomalies" in masked:
            masked["anomalies"] = [
                {**a, "message": mask_personal_info(a.get("message", ""))}
                for a in masked["anomalies"]
            ]
        return masked
    
    masked_anomalies = mask_anomalies(anomalies)

    # 스프레드시트 에디터용 데이터 (최대 100행)
    rows_data = parsed.get("rows", [])[:100]
    headers = parsed.get("headers", [])
    all_rows_with_headers = [
        {h: row[i] if i < len(row) else "" for i, h in enumerate(headers)}
        for row in rows_data
    ]

    result = {
        "status": "ok",
        "session_id": session_id,  # 클라이언트가 다운로드 시 사용
        "confidence": confidence,
        "anomalies": masked_anomalies,
        "duplicates": duplicates,
        "diagnostic_applied": bool(diagnostic_answers),
        "steps": {
            "parsed_summary": {
                "headers": parsed.get("headers", []),
                "row_count": len(parsed.get("rows", [])),
            },
            "all_rows": all_rows_with_headers,  # 스프레드시트 에디터용
            "matches": matches_for_response,  # 무시 컬럼 제외된 버전
            "validation": validation,
            "report": report,
        },
    }

    # 결과를 세션에 저장 (Excel 다운로드용)
    session_store.set(session_id, "validation_result", result)
    session_store.set(session_id, "parsed_data", parsed)

    # 성공 케이스 자동 저장 (Memory 시스템)
    if confidence.get("score", 0) >= 0.8:
        try:
            save_successful_case(
                headers=parsed.get("headers", []),
                matches=matches.get("matches", []),
                confidence=confidence.get("score", 0),
                was_auto_approved=True,
                metadata={"filename": file.filename}
            )
        except Exception as e:
            secure_logger.error(f"케이스 저장 실패: {e}")

    return result


@router.post("/react")
async def auto_validate_with_react(
    file: UploadFile = File(...),
    chatbot_answers: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(None)
) -> dict:
    """
    ReACT Agent를 사용한 자율적 파일 검증

    ReACT (Reasoning + Acting) 패턴:
    1. Think: 현재 상황 분석
    2. Act: 도구 실행
    3. Observe: 결과 확인, 신뢰도 체크
    4. 필요시 재시도 또는 사람에게 질문
    """
    # 세션 생성/조회
    session_id = session_store.get_or_create(x_session_id)

    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file is required")

    # 진단 답변 파싱
    diagnostic_answers = {}
    if chatbot_answers:
        try:
            diagnostic_answers = json.loads(chatbot_answers)
            session_store.set(session_id, "diagnostic_answers", diagnostic_answers)
        except json.JSONDecodeError:
            pass

    file_bytes = await file.read()

    # ReACT Agent 생성 및 실행
    registry = get_registry()
    agent = create_react_agent(registry, verbose=True)

    try:
        result = agent.run(
            file_bytes=file_bytes,
            diagnostic_answers=diagnostic_answers,
            sheet_type="재직자"
        )

        # 추론 과정 설명 추가
        result["agent_explanation"] = agent.explain_reasoning()
        result["session_id"] = session_id

        # 결과를 세션에 저장
        session_store.set(session_id, "validation_result", result)
        if result.get("steps", {}).get("parsed_summary"):
            parsed_data = {
                "headers": result["steps"]["parsed_summary"].get("headers", []),
                "rows": []
            }
            session_store.set(session_id, "parsed_data", parsed_data)

        # 성공 케이스 자동 저장
        confidence_score = result.get("confidence", {}).get("score", 0)
        if confidence_score >= 0.8:
            try:
                save_successful_case(
                    headers=result.get("steps", {}).get("parsed_summary", {}).get("headers", []),
                    matches=result.get("steps", {}).get("matches", {}).get("matches", []),
                    confidence=confidence_score,
                    was_auto_approved=result.get("status") == "completed",
                    metadata={"filename": file.filename, "mode": "react"}
                )
            except Exception as e:
                secure_logger.error(f"케이스 저장 실패: {e}")

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ReACT Agent 오류: {str(e)}"
        )


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
    # AI Agent가 도구를 사용해서 검증 (정확한 계산 + AI 판단)
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
        secure_logger.warning(f"AI Agent 분석 실패: {e}")

    return warnings


def _ai_agent_analyze(parsed: dict, answers: dict, row_count: int, headers: list, rows: list) -> dict:
    """
    AI Agent가 도구를 사용해서 데이터를 분석.
    - AI는 "뭘 확인할지" 판단
    - 실제 계산/비교는 도구(코드)가 수행
    """
    from internal.ai.llm_client import get_llm_client
    from internal.agent.tool_registry import (
        compare_headcount, check_date_order, find_duplicate_emp_ids, count_empty_rows
    )
    import json
    
    # rows가 list of list일 경우 dict로 변환
    rows_as_dicts = []
    if rows and headers:
        for row in rows:
            if isinstance(row, dict):
                rows_as_dicts.append(row)
            elif isinstance(row, (list, tuple)):
                row_dict = {}
                for i, val in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = val
                rows_as_dicts.append(row_dict)
    rows = rows_as_dicts
    
    # 헤더명에서 표준 컬럼 찾기 (부분 매칭)
    def find_column(row: dict, *targets) -> any:
        """여러 이름 중 하나라도 포함된 컬럼 값 반환"""
        for key, val in row.items():
            key_lower = str(key).lower().replace(" ", "")
            for t in targets:
                if t in key_lower:
                    return val
        return None
    rows = rows_as_dicts
    
    # ========================================
    # 1. 도구로 기본 검증 수행 (정확한 결과)
    # ========================================
    tool_results = {}
    issues = []
    
    # 인원수 비교
    headcount_questions = ["q19", "q20", "q21", "q22", "q23"]
    total_reported = sum(
        int(answers.get(q, 0)) 
        for q in headcount_questions 
        if str(answers.get(q, "")).isdigit()
    )
    if total_reported > 0:
        headcount_result = compare_headcount(total_reported, row_count)
        tool_results["headcount"] = headcount_result
        if not headcount_result.get("match"):
            issues.append({
                "severity": headcount_result.get("severity", "warning"),
                "message": headcount_result["message"]
            })
    
    # 중복 사원번호 체크
    if rows:
        dup_result = find_duplicate_emp_ids(rows, "사원번호")
        tool_results["duplicates"] = dup_result
        if dup_result.get("has_duplicates"):
            issues.append({
                "severity": "warning",
                "message": dup_result["message"]
            })
    
    # 빈 행 체크
    required_cols = ["사원번호", "생년월일", "입사일자", "기준급여"]
    if rows:
        empty_result = count_empty_rows(rows, required_cols)
        tool_results["empty_rows"] = empty_result
        if empty_result.get("has_empty"):
            issues.append({
                "severity": "info",
                "message": empty_result["message"]
            })
    
    # 날짜 순서 체크 - Layer1 validator에서 이미 수행하므로 중복 제거
    # (validation_layer1.py에서 입사나이, 날짜순서 등 체크함)
    # date_issues = [] ... (제거됨)
    
    # ========================================
    # 2. AI는 도구 결과를 바탕으로 "판단"만
    # ========================================
    try:
        client = get_llm_client()
        
        # 샘플 데이터 (AI에게 컨텍스트 제공)
        sample_data = []
        for row in rows[:5]:
            if isinstance(row, dict):
                sample_data.append({k: str(v)[:30] for k, v in list(row.items())[:6]})
        
        analysis_prompt = f"""당신은 재직자 명부 검증 결과를 해석하는 AI입니다.

## 도구 검증 결과 (이미 정확히 계산됨):
{json.dumps(tool_results, ensure_ascii=False, indent=2)}

## 발견된 이슈:
{json.dumps(issues, ensure_ascii=False, indent=2)}

## 고객 진단 답변:
{format_answers_for_ai(answers)}

## 샘플 데이터:
{json.dumps(sample_data, ensure_ascii=False)}

## 당신의 역할:
1) 도구 결과를 보고 **추가로 고객에게 확인이 필요한 사항**만 질문 생성
2) 숫자 비교, 형식 검증은 도구가 이미 했으므로 언급 금지
3) "비즈니스 판단"이 필요한 것만 질문
   예: "70세 입사자가 있는데 정상인가요?", "중복 사원번호 중 어느 것이 맞나요?"

## 응답 (JSON만):
{{
    "additional_issues": [
        {{"severity": "warning", "message": "추가 발견 사항 (있으면)"}}
    ],
    "questions_for_customer": [
        "비즈니스 판단이 필요한 질문만 (형식/숫자 질문 금지)"
    ]
}}"""

        response = client.chat([
            {"role": "system", "content": "검증 결과 해석 AI. JSON만 응답."},
            {"role": "user", "content": analysis_prompt}
        ])
        
        response_text = response.get("content", "").strip()
        
        # JSON 파싱
        import re
        if response_text.startswith("```"):
            lines = response_text.split("\n")[1:-1]
            response_text = "\n".join(lines)
        
        try:
            ai_result = json.loads(response_text)
        except:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    ai_result = json.loads(json_match.group())
                except:
                    ai_result = {}
            else:
                ai_result = {}
        
        # AI 추가 이슈 병합
        for issue in ai_result.get("additional_issues", []):
            if issue.get("message"):
                issues.append(issue)
        
        return {
            "issues": issues,
            "questions_for_customer": ai_result.get("questions_for_customer", []),
            "tool_results": tool_results
        }
        
    except Exception as e:
        # AI 호출 실패해도 도구 결과는 반환
        return {
            "issues": issues,
            "questions_for_customer": [],
            "tool_results": tool_results,
            "ai_error": str(e)
        }


@router.get("/download-excel")
async def download_excel(
    x_session_id: Optional[str] = Header(None)
):
    """검증 결과를 Excel 파일로 다운로드 (검증 리포트)

    x_session_id: 검증 시 받은 session_id 필요
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id 헤더가 필요합니다."
        )

    validation_result = session_store.get(x_session_id, "validation_result")
    parsed_data = session_store.get(x_session_id, "parsed_data")

    if not validation_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검증 결과가 없거나 세션이 만료되었습니다. 다시 검증해주세요."
        )

    try:
        excel_bytes = generate_excel_report(
            validation_result=validation_result,
            original_data=parsed_data
        )

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=validation_report.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel 생성 오류: {str(e)}"
        )


@router.get("/download-final-data")
async def download_final_data(
    x_session_id: Optional[str] = Header(None)
):
    """최종 수정본 다운로드 (매핑 완료된 깔끔한 데이터)

    x_session_id: 검증 시 받은 session_id 필요
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-Id 헤더가 필요합니다."
        )

    validation_result = session_store.get(x_session_id, "validation_result")
    parsed_data = session_store.get(x_session_id, "parsed_data")

    if not validation_result or not parsed_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="검증 결과가 없거나 세션이 만료되었습니다. 다시 검증해주세요."
        )

    try:
        excel_bytes = generate_final_data_excel(
            original_data=parsed_data,
            validation_result=validation_result
        )

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=final_data.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel 생성 오류: {str(e)}"
        )

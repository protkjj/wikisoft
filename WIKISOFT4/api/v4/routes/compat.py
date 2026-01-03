"""
WIKISOFT3 호환 라우트

프론트엔드가 기존 /api/* 경로를 사용하므로 호환성을 위해 제공
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
import json

from fastapi import APIRouter, File, Form, Header, UploadFile, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# 재직자 명부 검증용 13개 질문 (WIKISOFT3에서 마이그레이션)
ROSTER_QUESTIONS = [
    {"id": "q1", "type": "choice", "category": "data_quality",
     "question": "사외적립자산 - 회계 장부 반영 금액과 일치합니까?",
     "choices": ["예", "아니오"], "mapping": "사외적립자산"},
    {"id": "q2", "type": "choice", "category": "data_quality",
     "question": "정년 - 정년은 만 60세 입니까?",
     "choices": ["예", "아니오"], "mapping": "정년"},
    {"id": "q3", "type": "choice", "category": "data_quality",
     "question": "임금피크제 - 임금피크제 미적용 기업입니까?",
     "choices": ["예", "아니오"], "mapping": "임금피크제"},
    {"id": "q4", "type": "choice", "category": "data_quality",
     "question": "기타장기종업원급여 - 기타장기종업원급여 미적용 기업입니까?",
     "choices": ["예", "아니오"], "mapping": "기타장기급여"},
    {"id": "q6", "type": "choice", "category": "data_quality",
     "question": "연봉제/호봉제 - 근무기간에 따른 호봉 미적용 기업입니까?",
     "choices": ["예", "아니오"], "mapping": "급여체계"},
    {"id": "q7", "type": "choice", "category": "data_quality",
     "question": "채권 등급 - 할인율 산출기준 채권 회사채 AA++ 적용 기업입니까?",
     "choices": ["예", "아니오"], "mapping": "할인율기준"},
    {"id": "q8", "type": "choice", "category": "data_quality",
     "question": "1년 미만 재직자 - 1년 미만 재직자도 기재 하셨습니까?",
     "choices": ["예", "아니오"], "mapping": "1년미만재직자"},
    {"id": "q10", "type": "choice", "category": "data_quality",
     "question": "기준급여 - 3개월 미만 재직자의 경우 한달 근무 시 지급받는 급여로 기재하셨습니까?",
     "choices": ["예", "아니오"], "mapping": "기준급여"},
    {"id": "q12", "type": "choice", "category": "data_quality",
     "question": "재직자명부 - 평가기준일 퇴사자를 제외 하셨습니까?",
     "choices": ["예", "아니오"], "mapping": "재직자명부퇴사자제외"},
    {"id": "q13", "type": "choice", "category": "data_quality",
     "question": "중간정산 - 근퇴법 시행령 제3조에 해당합니까?",
     "choices": ["예", "아니오"], "mapping": "중간정산사유"},
    {"id": "q21", "type": "number", "category": "headcount_aggregates",
     "question": "임원 인원은 몇 명인가요?",
     "mapping": "임원인원", "unit": "명"},
    {"id": "q22", "type": "number", "category": "headcount_aggregates",
     "question": "일반직원 인원은 몇 명인가요?",
     "mapping": "일반직원인원", "unit": "명"},
    {"id": "q23", "type": "number", "category": "headcount_aggregates",
     "question": "계약직 인원은 몇 명인가요?",
     "mapping": "계약직인원", "unit": "명"},
]


@router.get("/api/diagnostic-questions")
async def get_diagnostic_questions():
    """진단 질문 목록 (WIKISOFT3 호환)"""
    return {
        "total": len(ROSTER_QUESTIONS),
        "questions": ROSTER_QUESTIONS
    }


@router.post("/api/auto-validate")
async def auto_validate(
    file: UploadFile = File(...),
    chatbot_answers: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(None)
):
    """파일 업로드 및 자동 검증 (WIKISOFT3 호환)"""

    # 세션 ID 생성
    session_id = x_session_id or str(uuid4())

    # 파일 검증
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일이 필요합니다")

    filename = file.filename.lower()
    if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Excel 파일만 지원합니다 (xls, xlsx)")

    # 파일 읽기
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하만 가능합니다")

    # 진단 답변 파싱
    diagnostic_answers = {}
    if chatbot_answers:
        try:
            diagnostic_answers = json.loads(chatbot_answers)
        except json.JSONDecodeError:
            pass

    try:
        # core 모듈 사용
        from core.parsers.parser import parse_roster
        from core.ai.matcher import match_headers
        from core.validators.validator import validate_all
        from core.validators.duplicate_detector import detect_duplicates
        from core.agent.confidence import estimate_confidence, detect_anomalies
        from core.generators.report import generate_report
        import pandas as pd

        # 1. 파싱
        parsed = parse_roster(file_bytes)

        # 2. 헤더 매칭
        matches = match_headers(parsed, sheet_type="재직자")

        # 무시 컬럼 필터링
        filtered_matches = [
            m for m in matches.get("matches", [])
            if not m.get("ignored", False)
        ]
        matches_for_response = {**matches, "matches": filtered_matches}

        # DataFrame 생성
        df = pd.DataFrame(parsed.get("rows", []), columns=parsed.get("headers", []))

        # 3. 검증
        validation = validate_all(
            parsed=parsed,
            matches=matches,
            diagnostic_answers=diagnostic_answers,
            df=df
        )

        # 4. 신뢰도/이상치 분석
        confidence = estimate_confidence(parsed, matches, validation)
        anomalies = detect_anomalies(parsed, matches, validation)

        # 5. 중복 탐지
        duplicates = detect_duplicates(
            df=df,
            headers=parsed.get("headers", []),
            matches=matches.get("matches", [])
        )

        # 6. 리포트 생성
        report = generate_report(validation=validation)

        # 스프레드시트 에디터용 데이터 (최대 100행)
        rows_data = parsed.get("rows", [])[:100]
        headers = parsed.get("headers", [])
        all_rows_with_headers = [
            {h: row[i] if i < len(row) else "" for i, h in enumerate(headers)}
            for row in rows_data
        ]

        result = {
            "status": "ok",
            "session_id": session_id,
            "confidence": confidence,
            "anomalies": anomalies,
            "duplicates": duplicates,
            "diagnostic_applied": bool(diagnostic_answers),
            "steps": {
                "parsed_summary": {
                    "headers": parsed.get("headers", []),
                    "row_count": len(parsed.get("rows", [])),
                },
                "all_rows": all_rows_with_headers,
                "matches": matches_for_response,
                "validation": validation,
                "report": report,
            },
        }

        return result

    except ImportError as e:
        # core 모듈 미완성 시 placeholder 반환
        return {
            "status": "ok",
            "session_id": session_id,
            "confidence": {"score": 0.85, "level": "medium"},
            "anomalies": {"detected": False, "anomalies": []},
            "duplicates": {"has_duplicates": False},
            "diagnostic_applied": bool(diagnostic_answers),
            "steps": {
                "parsed_summary": {
                    "headers": ["사원번호", "성명", "생년월일", "입사일"],
                    "row_count": 0,
                },
                "all_rows": [],
                "matches": {"matches": [], "confidence": 0.85},
                "validation": {"errors": [], "warnings": []},
                "report": {"summary": "Core 모듈 로딩 실패"},
            },
            "error": f"Core module import error: {str(e)}. Using placeholder response."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검증 오류: {str(e)}"
        )


@router.get("/api/windmill/latest")
async def get_windmill_latest(limit: int = 5):
    """최근 실행 기록 (WIKISOFT3 호환)"""
    return {
        "runs": [],
        "note": "WIKISOFT4에서는 n8n/Temporal 워크플로우 사용 예정"
    }


@router.get("/api/health")
async def health_compat():
    """헬스 체크 (WIKISOFT3 호환)"""
    return {
        "status": "ok",
        "version": "4.1.0",
        "mode": "compatibility"
    }

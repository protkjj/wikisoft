"""
AI 기반 검증 레이어
- knowledge_base 규칙 참조
- 진단 질문 응답 컨텍스트 고려
- 오류 패턴 학습
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd

from internal.ai.llm_client import LLMClient
from internal.ai.knowledge_base import get_error_check_rules, save_training_example


def call_llm(prompt: str, temperature: float = 0.2) -> str:
    """LLM 호출 유틸"""
    try:
        client = LLMClient()
        messages = [
            {"role": "system", "content": "당신은 HR 데이터 검증 전문가입니다. JSON 형식으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ]
        return client.chat(messages, temperature=temperature, max_tokens=2000)
    except Exception as e:
        return ""


def validate_with_ai(
    df: pd.DataFrame,
    matches: List[Dict],
    diagnostic_answers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    AI 기반 데이터 검증.
    
    Args:
        df: 검증할 DataFrame
        matches: 헤더 매핑 정보
        diagnostic_answers: 진단 질문 응답 (컨텍스트)
    
    Returns:
        errors, warnings, ai_reasoning
    """
    errors: List[Dict] = []
    warnings: List[Dict] = []
    ai_reasoning: List[str] = []
    
    # 1. 데이터 요약 생성
    data_summary = _create_data_summary(df, matches)
    
    # 2. 컨텍스트 구성
    context = _build_context(diagnostic_answers or {})
    
    # 3. 규칙 가져오기
    rules = get_error_check_rules()
    
    # 4. AI 프롬프트 구성
    prompt = f"""당신은 HR 데이터 검증 전문가입니다.
아래 규칙과 컨텍스트를 바탕으로 데이터를 검증하세요.

=== 검증 규칙 ===
{rules}

=== 회사 컨텍스트 ===
{context}

=== 데이터 요약 ===
{data_summary}

=== 중요 지시사항 ===
1. 샘플 데이터에서 **실제로 확인한 값만** 보고하세요.
2. 요약 통계를 보고 추측하지 마세요. 확실한 것만 보고하세요.
3. 문제가 없으면 errors와 warnings는 빈 배열([])로 반환하세요.
4. 기본 검증(음수, 형식 오류 등)은 이미 다른 레이어에서 처리됩니다.
5. 당신은 **데이터 간 관계**, **패턴 이상**, **맥락적 오류**만 찾으세요.
   예: "임원인데 급여가 일반 직원보다 낮음", "퇴직자인데 퇴직금이 0"
6. **행번호는 0-based index**로 반환하세요. (데이터 첫 행 = 0)

JSON 형식으로 응답하세요:
{{
    "errors": [
        {{"row": 행번호, "field": "필드명", "value": "실제값", "message": "오류 설명", "reason": "판단 근거"}}
    ],
    "warnings": [
        {{"row": 행번호, "field": "필드명", "value": "실제값", "message": "경고 설명", "reason": "판단 근거"}}
    ],
    "reasoning": "전체적인 검증 판단 설명 (문제 없으면 '검토 결과 특이사항 없음')"
}}
"""

    # 사원번호 컬럼 찾기 (emp_info 추가용)
    emp_col = None
    for m in matches:
        if m.get("target") == "사원번호" and m.get("source") in df.columns:
            emp_col = m["source"]
            break

    def mask_emp_id(emp_id: Any) -> str:
        """사원번호 (마스킹 비활성화)"""
        emp_str = str(emp_id) if emp_id else ""
        return emp_str or "(없음)"

    def add_emp_info(items: List[Dict]) -> List[Dict]:
        """에러/경고에 emp_info 추가 (AI는 0-based index로 응답)"""
        for item in items:
            row = item.get("row")
            if row is not None:
                try:
                    row_int = int(row)
                    # AI는 0-based index로 응답하므로 그대로 사용
                    row_idx = row_int if row_int >= 0 else 0
                    if emp_col and 0 <= row_idx < len(df):
                        emp_id = str(df.iloc[row_idx][emp_col]).strip()
                        # 소수점 제거 (float → int)
                        if '.' in emp_id:
                            emp_id = emp_id.split('.')[0]
                        item["emp_info"] = f"사원번호 {emp_id}"
                    else:
                        item["emp_info"] = f"행 {row_int + 2}"  # 엑셀 기준 행번호
                except:
                    item["emp_info"] = f"행 {row}"
        return items
    
    def normalize_field_name(field: str) -> str:
        """필드명 정규화 - L1과 AI의 필드명 통일
        
        예:
        - "입사연령" → "입사일자" (L1 필드명으로 통일)
        - "기준급여" ← "급여"
        """
        if not field:
            return field
        field = field.strip()
        
        # 입사 관련
        if "입사" in field and ("연령" in field or "나이" in field):
            return "입사일자"  # L1 필드명으로 통일
        
        # 급여 관련
        if "급여" in field:
            return "기준급여"  # L1 필드명으로 통일
        
        return field

    def normalize_items(items: List[Dict]) -> List[Dict]:
        """items의 field명을 정규화"""
        for item in items:
            if "field" in item:
                item["field"] = normalize_field_name(item["field"])
        return items

    # 5. AI 호출
    try:
        response = call_llm(prompt, temperature=0.1)
        
        if response:
            # JSON 파싱
            result = _parse_ai_response(response)
            
            if result:
                errors = add_emp_info(result.get("errors", []))
                warnings = add_emp_info(result.get("warnings", []))
                
                # 필드명 정규화 (L1과 맞추기)
                errors = normalize_items(errors)
                warnings = normalize_items(warnings)
                
                # L1에서 이미 처리하는 기본 검증은 제외
                # - 성별 값 오류
                # - 형식 오류
                errors = [e for e in errors if not (
                    "성별" in e.get("field", "") and ("값 오류" in e.get("message", "") or "형식" in e.get("message", ""))
                )]
                warnings = [w for w in warnings if not (
                    "성별" in w.get("field", "") and ("값 오류" in w.get("message", "") or "형식" in w.get("message", ""))
                )]
                
                ai_reasoning = [result.get("reasoning", "")]
                
                # 학습 데이터 저장
                save_training_example(
                    input_data={
                        "data_summary": data_summary,
                        "context": context,
                        "diagnostic_answers": diagnostic_answers
                    },
                    ai_response=result,
                    category="validation",
                    is_correct=True  # 나중에 사용자가 수정하면 False로 업데이트
                )
    except Exception as e:
        ai_reasoning.append(f"AI 검증 오류: {str(e)}")
    
    return {
        "errors": errors,
        "warnings": warnings,
        "ai_reasoning": ai_reasoning,
        "used_ai": True
    }


def _create_data_summary(df: pd.DataFrame, matches: List[Dict]) -> str:
    """데이터 요약 생성 (AI가 분석할 수 있도록)"""
    summary_parts = []
    
    # 기본 통계
    summary_parts.append(f"총 행 수: {len(df)}")
    summary_parts.append(f"컬럼 수: {len(df.columns)}")
    
    # 매핑된 필드 기준으로 통계
    mapping = {m["source"]: m["target"] for m in matches if m.get("target")}
    
    # 이상치 후보 추출
    anomalies = []
    
    for orig_col, std_col in mapping.items():
        if orig_col not in df.columns:
            continue
            
        col_data = df[orig_col]
        
        # 생년월일 분석
        if std_col in ["생년월일"]:
            try:
                # 연도 추출 시도
                years = col_data.dropna().astype(str).str[:4].astype(int, errors='ignore')
                if hasattr(years, 'min'):
                    min_year = years.min()
                    max_year = years.max()
                    if min_year < 1945:
                        anomalies.append(f"생년월일 최소: {min_year}년 (1945년 이전)")
                    if max_year > 2005:
                        anomalies.append(f"생년월일 최대: {max_year}년 (2005년 이후 = 20세 미만)")
            except:
                pass
        
        # 입사일 분석
        if std_col in ["입사일자", "입사일"]:
            try:
                # 미래 날짜 체크
                future_count = 0
                for val in col_data.dropna():
                    try:
                        if isinstance(val, (int, float)) and val > 50000:  # Excel 날짜로 2036년 이후
                            future_count += 1
                    except:
                        pass
                if future_count > 0:
                    anomalies.append(f"입사일 미래: {future_count}건")
            except:
                pass
        
        # 급여 분석
        if std_col in ["기준급여", "급여"]:
            try:
                salaries = pd.to_numeric(col_data, errors='coerce').dropna()
                if len(salaries) > 0:
                    min_sal = salaries.min()
                    max_sal = salaries.max()
                    neg_count = (salaries < 0).sum()
                    low_count = (salaries < 1900000).sum()
                    
                    if neg_count > 0:
                        anomalies.append(f"급여 음수: {neg_count}건")
                    if low_count > 0:
                        anomalies.append(f"급여 190만 미만: {low_count}건 (최저임금 미달 가능)")
                    summary_parts.append(f"급여 범위: {min_sal:,.0f} ~ {max_sal:,.0f}원")
            except:
                pass
        
        # 성별 분석
        if std_col in ["성별"]:
            try:
                unique_vals = col_data.dropna().unique()
                invalid = [v for v in unique_vals if str(v) not in ["1", "2", "1.0", "2.0", "남", "여", "M", "F"]]
                if invalid:
                    anomalies.append(f"성별 이상값: {invalid}")
            except:
                pass
        
        # 종업원구분 분석
        if std_col in ["종업원구분"]:
            try:
                value_counts = col_data.value_counts()
                summary_parts.append(f"종업원구분 분포: {dict(value_counts)}")
            except:
                pass
    
    if anomalies:
        summary_parts.append("\n=== 이상치 후보 ===")
        summary_parts.extend(anomalies)
    
    # 샘플 데이터 (처음 5행)
    summary_parts.append("\n=== 샘플 데이터 (처음 5행) ===")
    try:
        sample = df.head(5).to_dict('records')
        for i, row in enumerate(sample):
            # 주요 필드만
            row_summary = {k: v for k, v in row.items() if k in mapping}
            summary_parts.append(f"행{i+1}: {json.dumps(row_summary, ensure_ascii=False, default=str)}")
    except:
        pass
    
    return "\n".join(summary_parts)


def _build_context(diagnostic_answers: Dict[str, Any]) -> str:
    """진단 질문 응답을 컨텍스트로 변환"""
    if not diagnostic_answers:
        return "진단 질문 응답 없음 (기본 규칙 적용)"
    
    context_parts = []
    
    # 주요 진단 응답 해석
    mappings = {
        "has_pension_assets": ("사외적립자산 있음", "사외적립자산 없음"),
        "has_retirement_age": ("정년 있음", "정년 없음"),
        "has_salary_peak": ("임금피크제 있음", "임금피크제 없음"),
        "has_long_term_benefits": ("기타장기종업원급여 있음", "기타장기종업원급여 없음"),
        "is_annual_salary": ("연봉제", "호봉제"),
        "excludes_resigned": ("퇴사자 제외됨", "퇴사자 포함"),
    }
    
    for key, (yes_text, no_text) in mappings.items():
        if key in diagnostic_answers:
            val = diagnostic_answers[key]
            if val in [True, "예", "yes", "Y"]:
                context_parts.append(f"- {yes_text}")
            elif val in [False, "아니오", "no", "N"]:
                context_parts.append(f"- {no_text}")
    
    # 인원수 정보
    for key in ["executive_count", "employee_count", "contract_count"]:
        if key in diagnostic_answers:
            name = {"executive_count": "임원", "employee_count": "일반직원", "contract_count": "계약직"}[key]
            context_parts.append(f"- {name} 인원: {diagnostic_answers[key]}명")
    
    if not context_parts:
        return "진단 질문 응답: (구체적 정보 없음)"
    
    return "\n".join(context_parts)


def _parse_ai_response(response: str) -> Optional[Dict]:
    """AI 응답에서 JSON 추출"""
    try:
        # JSON 블록 찾기
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        # { } 찾기
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        return json.loads(response)
    except json.JSONDecodeError:
        return None


def save_error_correction(
    original_errors: List[Dict],
    corrected_errors: List[Dict],
    diagnostic_answers: Dict[str, Any]
) -> str:
    """
    사용자가 AI 오류를 수정했을 때 학습 데이터 저장.
    
    Args:
        original_errors: AI가 원래 찾은 오류
        corrected_errors: 사용자가 수정한 오류 (일부 제거/추가)
        diagnostic_answers: 진단 질문 응답
    
    Returns:
        저장된 파일 경로
    """
    return save_training_example(
        input_data={
            "diagnostic_answers": diagnostic_answers,
            "original_errors": original_errors
        },
        ai_response={"errors": original_errors},
        human_correction={"errors": corrected_errors},
        is_correct=False,  # AI가 틀렸으므로
        category="validation_correction"
    )

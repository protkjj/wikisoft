from typing import Any, Dict, List, Optional
import json
import logging
import os
import re
from difflib import SequenceMatcher

from core.parsers.standard_schema import STANDARD_SCHEMA, get_required_fields
from core.memory.case_store import get_few_shot_examples, save_successful_case

logger = logging.getLogger(__name__)


# 매핑 불필요한 컬럼 (무시할 헤더 키워드)
IGNORE_HEADERS = [
    "참고사항", "비고란", "메모", "note", "remark", "comment",
    "unnamed", "column", "컬럼"
]


def _should_ignore(header: str) -> bool:
    """매핑 불필요한 컬럼인지 확인."""
    h_lower = header.lower().strip()
    if not h_lower:
        return True
    for ignore_kw in IGNORE_HEADERS:
        if h_lower == ignore_kw or h_lower.startswith(ignore_kw):
            return True
        # "unnamed"는 부분 일치도 허용
        if ignore_kw == "unnamed" and "unnamed" in h_lower:
            return True
    return False


def _normalize(header: str) -> str:
    h = header.replace("\n", " ")
    h = re.sub(r"\([^)]*\)", "", h)
    h = re.sub(r"\s+", " ", h)
    return h.lower().strip()


def _rule_match(headers: List[str], sheet_type: str = "all") -> Dict[str, Any]:
    schema = {
        name: meta
        for name, meta in STANDARD_SCHEMA.items()
        if meta.get("sheet") == sheet_type or sheet_type == "all"
    }

    matches = []
    warnings = []

    for h in headers:
        # 무시할 컬럼은 스킵
        if _should_ignore(h):
            matches.append({"source": h, "target": None, "confidence": 0.0, "ignored": True})
            continue
            
        h_norm = _normalize(h)
        best = None
        best_score = 0.0
        for field_name, meta in schema.items():
            field_norm = _normalize(field_name)
            score = SequenceMatcher(None, h_norm, field_norm).ratio()
            if score > best_score:
                best_score = score
                best = field_name
            for alias in meta.get("aliases", []):
                alias_norm = _normalize(alias)
                score = SequenceMatcher(None, h_norm, alias_norm).ratio()
                if score > best_score:
                    best_score = score
                    best = field_name
        if best and best_score >= 0.65:
            matches.append({"source": h, "target": best, "confidence": round(best_score, 3), "fallback": True})
        else:
            matches.append({"source": h, "target": None, "confidence": 0.0, "unmapped": True, "fallback": True})
            warnings.append(f"unmapped header: {h}")

    return {"matches": matches, "warnings": warnings}


def ai_match_columns(headers: List[str], sheet_type: str = "all", api_key: Optional[str] = None) -> Dict[str, Any]:
    """AI 매칭 호출 (OpenAI) + Few-shot Learning. 키 없으면 폴백 사용."""
    api_key_to_use = api_key or os.getenv("OPENAI_API_KEY")
    schema = {
        name: meta
        for name, meta in STANDARD_SCHEMA.items()
        if meta.get("sheet") == sheet_type or sheet_type == "all"
    }

    if not api_key_to_use:
        return {**_rule_match(headers, sheet_type), "used_ai": False, "warnings": ["OPENAI_API_KEY missing, fallback matcher used"]}

    # Few-shot 예제 가져오기 (과거 성공 케이스)
    few_shot_examples = get_few_shot_examples(headers, k=3)
    few_shot_prompt = ""
    if few_shot_examples:
        few_shot_prompt = "\n\n### 과거 성공 매칭 예제 (참고용):\n"
        for i, ex in enumerate(few_shot_examples, 1):
            few_shot_prompt += f"예제 {i}:\n"
            few_shot_prompt += f"  입력 헤더: {ex['input_headers'][:5]}\n"
            few_shot_prompt += f"  매칭 결과: {ex['output_matches'][:5]}\n"
            if ex.get("human_corrections"):
                few_shot_prompt += f"  (사람 수정: {ex['human_corrections']})\n"

    prompt = f"""
당신은 HR 데이터 스키마 매칭 전문가입니다. 고객 헤더를 표준 스키마에 매핑하세요.

고객 헤더: {json.dumps(headers, ensure_ascii=False)}
표준 스키마: {json.dumps(schema, ensure_ascii=False)}
{few_shot_prompt}
규칙:
1) 가장 의미적으로 가까운 필드에 매칭, aliases 참고
2) 확실치 않으면 unmapped
3) confidence 0.0~1.0
4) JSON만 반환
응답 형식:
{{
  "mappings": [{{"customer_header": "사번", "standard_field": "사원번호", "confidence": 0.95}}],
  "unmapped": ["비고"]
}}
"""

    try:
        from openai import OpenAI
        import openai

        client = OpenAI(api_key=api_key_to_use)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "HR 데이터 스키마 매칭만 수행하고 JSON으로만 응답"},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        data = json.loads(content)
    except openai.OpenAIError as e:
        # OpenAI API 오류 (네트워크, 인증 등)
        logger.warning(f"OpenAI API 오류: {e}", exc_info=True)
        return {
            **_rule_match(headers, sheet_type),
            "used_ai": False,
            "warnings": ["AI 매칭 실패 (API 오류), rule-based fallback 사용"]
        }
    except json.JSONDecodeError as e:
        # AI 응답 JSON 파싱 실패
        logger.error(f"AI 응답 JSON 파싱 실패: {content[:100] if 'content' in locals() else 'N/A'}", exc_info=True)
        return {
            **_rule_match(headers, sheet_type),
            "used_ai": False,
            "warnings": ["AI 응답 형식 오류, fallback 사용"]
        }
    except Exception as e:
        # 예상치 못한 오류
        logger.exception(f"예상치 못한 매칭 오류: {e}")
        return {
            **_rule_match(headers, sheet_type),
            "used_ai": False,
            "warnings": ["매칭 오류 발생, fallback 사용"]
        }

    mappings = []
    warnings = []
    for m in data.get("mappings", []):
        mappings.append({
            "source": m.get("customer_header"),
            "target": m.get("standard_field"),
            "confidence": m.get("confidence", 0),
            "reason": m.get("reason", ""),
            "used_ai": True,
        })

    for unmapped in data.get("unmapped", []):
        mappings.append({"source": unmapped, "target": None, "confidence": 0.0, "unmapped": True, "used_ai": True})

    # 필수 필드 누락 경고는 match_headers에서 최종 체크 (Few-shot 병합 후)

    return {
        "matches": mappings,
        "warnings": warnings,
        "used_ai": True,
    }


def match_headers(parsed: Dict[str, Any], sheet_type: str = "all", retry: bool = False) -> Dict[str, Any]:
    """
    헤더 매칭 (Few-shot 자동 조회 포함).
    
    Args:
        parsed: 파싱된 데이터
        sheet_type: 시트 타입 (기본 "all"로 모든 필드 포함)
        retry: 재시도 여부 (True면 Few-shot 강화)
    """
    headers = parsed.get("headers", [])
    use_ai = os.getenv("OPENAI_API_KEY") is not None
    
    # 무시할 컬럼 먼저 분리
    ignored_headers = [h for h in headers if _should_ignore(h)]
    active_headers = [h for h in headers if not _should_ignore(h)]
    
    # Few-shot 예제 먼저 적용 (학습된 케이스에서 직접 매핑)
    few_shot_mappings = _apply_few_shot_mappings(active_headers)
    
    if few_shot_mappings:
        # Few-shot으로 이미 매핑된 것들 우선 사용
        remaining_headers = [h for h in active_headers if h not in few_shot_mappings]
        
        if not remaining_headers:
            # 모든 활성 헤더가 Few-shot으로 매핑됨
            matches = []
            # 무시 컬럼 먼저 추가
            for h in ignored_headers:
                matches.append({"source": h, "target": None, "confidence": 0.0, "ignored": True})
            # Few-shot 매핑 추가
            for h in active_headers:
                matches.append({
                    "source": h, "target": few_shot_mappings[h], 
                    "confidence": 0.95, "from_fewshot": True
                })
            return {
                "columns": headers,
                "matches": matches,
                "warnings": [],
                "used_ai": False,
                "used_fewshot": True,
            }
    else:
        remaining_headers = active_headers
        few_shot_mappings = {}
    
    # 나머지는 AI 또는 규칙 기반 매칭
    if use_ai and remaining_headers:
        result = ai_match_columns(remaining_headers, sheet_type=sheet_type)
    else:
        result = _rule_match(remaining_headers, sheet_type)
    
    # Few-shot 결과와 병합, 무시 컬럼 포함
    final_matches = []
    
    # 무시 컬럼 먼저 추가
    for h in ignored_headers:
        final_matches.append({"source": h, "target": None, "confidence": 0.0, "ignored": True})
    
    # 활성 헤더들 처리
    for h in active_headers:
        if h in few_shot_mappings:
            final_matches.append({
                "source": h, 
                "target": few_shot_mappings[h], 
                "confidence": 0.95, 
                "from_fewshot": True
            })
        else:
            # AI/규칙 매칭 결과에서 찾기
            found = False
            for m in result.get("matches", []):
                if m.get("source") == h:
                    final_matches.append(m)
                    found = True
                    break
            if not found:
                final_matches.append({"source": h, "target": None, "confidence": 0.0, "unmapped": True})
    
    # 필수 필드 누락 경고 추가 (final_matches 기준으로 체크)
    warnings = result.get("warnings", [])
    required = set(get_required_fields(sheet_type))
    mapped_targets = {m["target"] for m in final_matches if m.get("target")}
    missing_required = list(required - mapped_targets)
    if missing_required:
        warnings.append(f"필수 필드 누락: {', '.join(missing_required)}")
    
    return {
        "columns": headers,
        "matches": final_matches,
        "warnings": warnings,
        "used_ai": result.get("used_ai", use_ai),
        "used_fewshot": bool(few_shot_mappings),
    }


def _apply_few_shot_mappings(headers: List[str]) -> Dict[str, str]:
    """
    Few-shot 케이스에서 학습된 매핑 적용.
    
    저장된 케이스를 조회해서 동일 헤더가 있으면 그 매핑을 사용.
    """
    from core.memory.case_store import CaseStore
    
    try:
        store = CaseStore()
        mappings = {}
        
        for header in headers:
            # 헤더와 일치하는 케이스 찾기
            similar_cases = store.find_by_header(header)
            if similar_cases:
                # 가장 최근 케이스의 매핑 사용
                for case in similar_cases:
                    for match in case.get("matches", []):
                        if match.get("source") == header and match.get("target"):
                            mappings[header] = match["target"]
                            break
                    if header in mappings:
                        break
        
        return mappings
    except Exception:
        return {}


def ask_dynamic_questions(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = context.get("matches", {}).get("matches") if isinstance(context.get("matches"), dict) else context.get("matches", [])
    warnings = context.get("matches", {}).get("warnings") if isinstance(context.get("matches"), dict) else context.get("warnings", [])
    questions: List[Dict[str, Any]] = []

    for m in matches or []:
        if m.get("unmapped"):
            questions.append({
                "id": f"clarify_{m['source']}",
                "type": "text",
                "category": "clarification",
                "question": f"'{m['source']}' 컬럼의 의미/매핑 대상을 알려주세요.",
            })

    for w in warnings or []:
        questions.append({
            "id": f"warn_{len(questions)+1}",
            "type": "text",
            "category": "warning",
            "question": f"추가 확인: {w}",
        })

    return questions

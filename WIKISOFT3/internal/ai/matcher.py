from typing import Any, Dict, List, Optional
import json
import os
import re
from difflib import SequenceMatcher

from internal.parsers.standard_schema import STANDARD_SCHEMA, get_required_fields
from internal.memory.case_store import get_few_shot_examples, save_successful_case


def _normalize(header: str) -> str:
    h = header.replace("\n", " ")
    h = re.sub(r"\([^)]*\)", "", h)
    h = re.sub(r"\s+", " ", h)
    return h.lower().strip()


def _rule_match(headers: List[str], sheet_type: str = "재직자") -> Dict[str, Any]:
    schema = {
        name: meta
        for name, meta in STANDARD_SCHEMA.items()
        if meta.get("sheet") == sheet_type or sheet_type == "all"
    }

    matches = []
    warnings = []

    for h in headers:
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


def ai_match_columns(headers: List[str], sheet_type: str = "재직자", api_key: Optional[str] = None) -> Dict[str, Any]:
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
    except Exception as e:  # noqa: BLE001
        return {**_rule_match(headers, sheet_type), "used_ai": False, "warnings": [f"AI 매칭 실패, fallback 사용: {e}"]}

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

    # 필수 필드 누락 경고
    required = set(get_required_fields(sheet_type))
    mapped_targets = {m["target"] for m in mappings if m.get("target")}
    missing_required = list(required - mapped_targets)
    if missing_required:
        warnings.append(f"필수 필드 누락: {', '.join(missing_required)}")

    return {
        "matches": mappings,
        "warnings": warnings,
        "used_ai": True,
    }


def match_headers(parsed: Dict[str, Any], sheet_type: str = "재직자") -> Dict[str, Any]:
    headers = parsed.get("headers", [])
    use_ai = os.getenv("OPENAI_API_KEY") is not None
    result = ai_match_columns(headers, sheet_type=sheet_type) if use_ai else _rule_match(headers, sheet_type)
    return {
        "columns": headers,
        "matches": result.get("matches", []),
        "warnings": result.get("warnings", []),
        "used_ai": result.get("used_ai", use_ai),
    }


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

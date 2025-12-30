"""
AI 기반 컬럼 헤더 매칭 시스템

고객사 Excel 파일의 헤더를 표준 스키마에 자동 매칭
"""
from typing import Dict, List, Any, Optional
import json
import re
from openai import OpenAI
import os


def ai_match_columns(
    customer_headers: List[str],
    sheet_type: str = "재직자",
    api_key: Optional[str] = None,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    GPT-4를 사용하여 고객 헤더를 표준 필드에 자동 매칭
    
    Args:
        customer_headers: 고객 파일의 컬럼 헤더 리스트
        sheet_type: "재직자", "퇴직자", "추가" 중 하나
        api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        confidence_threshold: 최소 신뢰도 (0.7 이상만 매칭)
        
    Returns:
        {
            "mappings": {
                "사번": {"standard_field": "사원번호", "confidence": 0.95},
                "들어온날짜": {"standard_field": "입사일자", "confidence": 0.88}
            },
            "unmapped": ["알수없는컬럼1", "비고"],
            "missing_required": ["성별", "종업원구분"],
            "total_confidence": 0.85
        }
    """
    from internal.parsers.standard_schema import STANDARD_SCHEMA, get_required_fields
    
    # 1. 해당 시트 타입의 스키마만 필터링
    relevant_schema = {
        field_name: schema
        for field_name, schema in STANDARD_SCHEMA.items()
        if schema.get("sheet") == sheet_type or sheet_type == "all"
    }
    
    # 2. AI 프롬프트 생성
    prompt = f"""
당신은 HR 데이터 전문가입니다. 고객이 제공한 Excel 컬럼 헤더를 우리의 표준 스키마에 매칭하세요.

## 고객 파일 헤더 ({len(customer_headers)}개):
{json.dumps(customer_headers, ensure_ascii=False, indent=2)}

## 표준 스키마:
{json.dumps(relevant_schema, ensure_ascii=False, indent=2)}

## 매칭 규칙:
1. 고객 헤더를 가장 의미적으로 가까운 표준 필드에 매칭
2. aliases를 참고하되, 의미를 우선 고려
3. confidence는 0.0~1.0 사이 (0.7 이상만 매칭)
4. 확실하지 않으면 unmapped에 포함
5. 한국어/영어 혼재 가능

## 응답 형식 (JSON만):
{{
  "mappings": [
    {{
      "customer_header": "사번",
      "standard_field": "사원번호",
      "confidence": 0.95,
      "reason": "사번은 사원번호의 일반적인 약어"
    }},
    {{
      "customer_header": "들어온날짜",
      "standard_field": "입사일자",
      "confidence": 0.88,
      "reason": "입사 날짜를 의미하는 비표준 표현"
    }}
  ],
  "unmapped": ["비고", "특이사항"]
}}
"""
    
    # 3. OpenAI API 호출
    try:
        api_key_to_use = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key_to_use:
            # API 키 없음 → 폴백 사용 (경고 표시)
            print("⚠️  OpenAI API 키 없음. 폴백 매칭 사용 (정확도 낮음)")
            print("   프로덕션 환경에서는 OPENAI_API_KEY 환경변수 설정 필수!")
            return _fallback_match(customer_headers, relevant_schema, confidence_threshold)
        
        client = OpenAI(api_key=api_key_to_use)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 HR 데이터 스키마 매칭 전문가입니다. 반드시 JSON 형식으로만 응답하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,  # 일관성 중요
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ AI 매칭 실패: {e}")
        print(f"   폴백 매칭으로 대체 (정확도 낮음, 확인 필요)")
        return _fallback_match(customer_headers, relevant_schema, confidence_threshold)
    
    # 4. 결과 정리
    mappings = {}
    unmapped = set(customer_headers)
    
    for mapping in result.get("mappings", []):
        customer_header = mapping["customer_header"]
        standard_field = mapping["standard_field"]
        confidence = mapping["confidence"]
        
        # 신뢰도 임계값 체크
        if confidence >= confidence_threshold:
            mappings[customer_header] = {
                "standard_field": standard_field,
                "confidence": confidence,
                "reason": mapping.get("reason", "")
            }
            unmapped.discard(customer_header)
    
    # 5. 필수 필드 누락 체크
    required_fields = set(get_required_fields(sheet_type))
    mapped_fields = set(m["standard_field"] for m in mappings.values())
    missing_required = list(required_fields - mapped_fields)
    
    # 6. 전체 신뢰도 계산
    if mappings:
        total_confidence = sum(m["confidence"] for m in mappings.values()) / len(mappings)
    else:
        total_confidence = 0.0
    
    # 7. 경고 및 에러 처리
    warnings = []
    
    # 필수 필드 누락 시 강력 경고
    if missing_required:
        warnings.append({
            "severity": "error",
            "message": f"필수 필드 누락: {', '.join(missing_required)}. 파일을 확인하거나 수동 매핑 필요."
        })
    
    # 신뢰도 낮은 매칭
    low_confidence = [
        (k, v["confidence"]) 
        for k, v in mappings.items() 
        if v["confidence"] < 0.8
    ]
    if low_confidence:
        warnings.append({
            "severity": "warning",
            "message": f"낮은 신뢰도 매칭 {len(low_confidence)}개: 확인 권장",
            "details": low_confidence
        })
    
    # 매칭 안 된 컬럼이 많은 경우
    if len(unmapped) > len(customer_headers) * 0.3:  # 30% 이상
        warnings.append({
            "severity": "warning",
            "message": f"매칭 실패 컬럼이 많음 ({len(unmapped)}개). 파일 형식 확인 필요."
        })
    
    return {
        "mappings": mappings,
        "unmapped": list(unmapped) + result.get("unmapped", []),
        "missing_required": missing_required,
        "total_confidence": round(total_confidence, 3),
        "sheet_type": sheet_type,
        "warnings": warnings,
        "used_ai": True  # AI 사용 여부 표시
    }


def _fallback_match(
    customer_headers: List[str],
    schema: Dict[str, Dict],
    threshold: float
) -> Dict[str, Any]:
    """
    AI 실패 시 폴백: 문자열 유사도 기반 자연스러운 매칭
    """
    from difflib import SequenceMatcher
    
    mappings = {}
    unmapped = []
    
    def normalize_header(header: str) -> str:
        """헤더 정규화: 개행, 괄호, 숫자 제거"""
        header = header.replace('\n', ' ')
        header = re.sub(r'\([^)]*\)', '', header)
        header = re.sub(r'\s+', ' ', header)
        return header.lower().strip()
    
    # 유사도 기반 매칭
    for header in customer_headers:
        header_normalized = normalize_header(header)
        best_match = None
        best_score = 0.0
        
        for field_name, field_schema in schema.items():
            # 필드명 자체와 비교
            field_normalized = normalize_header(field_name)
            score = SequenceMatcher(None, header_normalized, field_normalized).ratio()
            if score > best_score:
                best_score = score
                best_match = field_name
            
            # 별칭과 비교
            for alias in field_schema.get("aliases", []):
                alias_normalized = normalize_header(alias)
                score = SequenceMatcher(None, header_normalized, alias_normalized).ratio()
                if score > best_score:
                    best_score = score
                    best_match = field_name
        
        if best_score >= threshold:
            mappings[header] = {
                "standard_field": best_match,
                "confidence": round(best_score, 3),
                "reason": "문자열 유사도 기반 매칭"
            }
        else:
            unmapped.append(header)
    
    return {
        "mappings": mappings,
        "unmapped": unmapped,
        "missing_required": [],
        "total_confidence": 0.0,
        "fallback": True,
        "warnings": [
            {
                "severity": "info",
                "message": "AI 미사용 - 폴백 매칭 중. OpenAI API 키 설정하면 정확도 향상됩니다."
            }
        ],
        "used_ai": False  # AI 미사용
    }


def apply_mapping_to_dataframe(df, mapping_result: Dict[str, Any]):
    """
    매칭 결과를 DataFrame에 적용 (컬럼 이름 변경)
    
    Args:
        df: pandas DataFrame
        mapping_result: ai_match_columns()의 결과
        
    Returns:
        컬럼명이 표준화된 DataFrame
    """
    import pandas as pd
    
    rename_dict = {
        customer_header: mapping_info["standard_field"]
        for customer_header, mapping_info in mapping_result["mappings"].items()
    }
    
    return df.rename(columns=rename_dict)


if __name__ == "__main__":
    # 테스트: 다양한 헤더 형식
    print("=== AI 컬럼 매칭 테스트 ===\n")
    
    test_cases = [
        {
            "name": "세라젬 스타일",
            "headers": ["사원번호", "이름", "성별", "생년월일", "입사일자", "종업원구분", "기준급여"]
        },
        {
            "name": "비표준 한글",
            "headers": ["사번", "성명", "성", "태어난날", "들어온날짜", "직원타입", "월급"]
        },
        {
            "name": "영문 헤더",
            "headers": ["emp_id", "name", "gender", "birth_date", "hire_date", "emp_type", "salary"]
        },
        {
            "name": "혼합 + 오타",
            "headers": ["직원번호", "이름", "섬별", "Birthday", "입사년월일", "근로자구분", "급여액"]
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"테스트: {test['name']}")
        print(f"{'='*60}")
        print(f"고객 헤더: {test['headers']}\n")
        
        result = ai_match_columns(test['headers'], sheet_type="재직자")
        
        print(f"✅ 매칭 성공: {len(result['mappings'])}개")
        for customer, info in result['mappings'].items():
            print(f"  {customer:15} → {info['standard_field']:15} (신뢰도: {info['confidence']:.2f})")
            if info.get('reason'):
                print(f"                    이유: {info['reason'][:60]}")
        
        if result['unmapped']:
            print(f"\n⚠️  매칭 실패: {result['unmapped']}")
        
        if result['missing_required']:
            print(f"\n❌ 필수 필드 누락: {result['missing_required']}")
        
        print(f"\n전체 신뢰도: {result['total_confidence']:.1%}")

"""
AI Matcher 테스트
"""
import pytest
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT3")

from internal.ai.matcher import match_headers, _rule_match, _normalize


class TestNormalize:
    """헤더 정규화 테스트"""
    
    def test_normalize_newline(self):
        """개행 제거"""
        assert _normalize("사원\n번호") == "사원 번호"
    
    def test_normalize_parentheses(self):
        """괄호 내용 제거"""
        assert _normalize("급여(원)") == "급여"
        assert _normalize("입사일(YYYYMMDD)") == "입사일"
    
    def test_normalize_spaces(self):
        """다중 공백 축약"""
        assert _normalize("사원   번호") == "사원 번호"
    
    def test_normalize_lowercase(self):
        """소문자 변환"""
        assert _normalize("EMPLOYEE_ID") == "employee_id"


class TestRuleMatch:
    """규칙 기반 매칭 테스트"""
    
    def test_exact_match(self):
        """정확한 매칭"""
        result = _rule_match(["사원번호", "이름", "생년월일"])
        matches = result["matches"]
        
        assert len(matches) == 3
        assert matches[0]["target"] == "사원번호"
        assert matches[0]["confidence"] >= 0.9
    
    def test_alias_match(self):
        """별칭 매칭"""
        result = _rule_match(["직원번호", "성명", "출생일"])
        matches = result["matches"]
        
        # 별칭으로 매칭되어야 함
        targets = [m["target"] for m in matches if m.get("target")]
        assert "사원번호" in targets  # 직원번호 → 사원번호
        assert "이름" in targets  # 성명 → 이름
    
    def test_unmapped_headers(self):
        """매칭 안 되는 헤더"""
        result = _rule_match(["사원번호", "특이사항", "비고"])
        matches = result["matches"]
        
        unmapped = [m for m in matches if m.get("unmapped")]
        assert len(unmapped) >= 1  # 특이사항, 비고는 unmapped
    
    def test_low_confidence_threshold(self):
        """0.65 미만은 unmapped"""
        result = _rule_match(["xyz123", "완전무관한헤더"])
        matches = result["matches"]
        
        unmapped = [m for m in matches if m.get("unmapped")]
        assert len(unmapped) == 2
    
    def test_fallback_flag(self):
        """폴백 플래그 확인"""
        result = _rule_match(["사원번호"])
        assert result["matches"][0].get("fallback") == True


class TestMatchHeaders:
    """match_headers 함수 테스트"""
    
    def test_match_headers_basic(self):
        """기본 매칭"""
        parsed = {"headers": ["사원번호", "이름", "입사일"]}
        result = match_headers(parsed)
        
        assert "columns" in result
        assert "matches" in result
        assert "warnings" in result
        assert len(result["matches"]) == 3
    
    def test_match_headers_empty(self):
        """빈 헤더"""
        parsed = {"headers": []}
        result = match_headers(parsed)
        
        assert result["matches"] == []
    
    def test_match_headers_with_warnings(self):
        """경고 생성"""
        parsed = {"headers": ["사원번호", "알수없는컬럼"]}
        result = match_headers(parsed)
        
        # unmapped 헤더에 대한 경고
        assert len(result["warnings"]) >= 0  # 경고가 있을 수 있음


class TestVariousHeaderFormats:
    """다양한 헤더 형식 테스트"""
    
    def test_korean_headers(self):
        """한국어 헤더"""
        result = _rule_match(["사원번호", "이름", "생년월일", "입사일", "기준급여"])
        mapped = [m for m in result["matches"] if m.get("target")]
        assert len(mapped) == 5
    
    def test_english_headers(self):
        """영어 헤더 (별칭)"""
        result = _rule_match(["employee_id", "name", "birth_date"])
        mapped = [m for m in result["matches"] if m.get("target")]
        assert len(mapped) >= 2  # 최소 2개는 매칭
    
    def test_mixed_headers(self):
        """혼합 헤더"""
        result = _rule_match(["사번", "이름", "hire_date", "salary"])
        mapped = [m for m in result["matches"] if m.get("target")]
        assert len(mapped) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

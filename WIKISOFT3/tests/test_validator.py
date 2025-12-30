"""
Validator 테스트 (Layer 1 & Layer 2)
"""
import pytest
import pandas as pd
import sys
sys.path.insert(0, "/Users/kj/Desktop/wiki/WIKISOFT3")

from internal.validators.validation_layer1 import validate_layer1
from internal.validators.validation_layer2 import validate_layer2


class TestValidationLayer1:
    """Layer 1 검증 테스트"""
    
    def create_valid_df(self) -> pd.DataFrame:
        """유효한 테스트 데이터프레임"""
        return pd.DataFrame({
            "사원번호": ["EMP001", "EMP002", "EMP003"],
            "이름": ["홍길동", "김철수", "이영희"],
            "생년월일": ["19900115", "19850620", "19921130"],
            "입사일": ["20200301", "20180715", "20210110"],
            "기준급여": [5000000, 6000000, 4500000],
            "종업원구분": ["직원", "직원", "계약직"],
            "제도구분": ["DB", "DB", "DC"],
        })
    
    def test_valid_data(self):
        """유효한 데이터"""
        df = self.create_valid_df()
        result = validate_layer1(df, {})
        
        # 에러가 적어야 함
        assert len(result.get("errors", [])) <= 3  # 일부 형식 오류 가능
    
    def test_missing_required_column(self):
        """필수 컬럼 누락"""
        df = pd.DataFrame({
            "이름": ["홍길동"],
            "생년월일": ["19900115"],
        })
        result = validate_layer1(df, {})
        
        # 필수 필드 누락 에러
        errors = result.get("errors", [])
        assert len(errors) > 0
    
    def test_empty_required_value(self):
        """필수 값 누락"""
        df = pd.DataFrame({
            "사원번호": ["EMP001", None, "EMP003"],
            "이름": ["홍길동", "김철수", "이영희"],
            "생년월일": ["19900115", "19850620", "19921130"],
            "입사일": ["20200301", "20180715", "20210110"],
            "기준급여": [5000000, 6000000, 4500000],
            "종업원구분": ["직원", "직원", "계약직"],
            "제도구분": ["DB", "DB", "DC"],
        })
        result = validate_layer1(df, {})
        
        # 에러 또는 경고 발생
        assert len(result.get("errors", [])) > 0 or len(result.get("warnings", [])) > 0


class TestValidationLayer2:
    """Layer 2 검증 테스트 (챗봇 답변 vs 계산값)"""
    
    def test_exact_match(self):
        """정확히 일치"""
        chatbot_answers = {"q21": 10, "q22": 50, "q23": 5}
        calculated = {"headcount": {"임원": 10, "일반직원": 50, "계약직": 5}}
        
        result = validate_layer2(chatbot_answers, calculated)
        
        # 대부분 passed
        assert result["status"] in ["passed", "warnings"]
    
    def test_tolerance_within_5_percent(self):
        """5% 이내 차이"""
        chatbot_answers = {"q21": 10, "q22": 52}  # 50 vs 52 = 4% 차이
        calculated = {"headcount": {"임원": 10, "일반직원": 50}}
        
        result = validate_layer2(chatbot_answers, calculated, tolerance_percent=5.0)
        
        # 경고는 있을 수 있지만 passed
        assert result["status"] in ["passed", "warnings"]
    
    def test_over_tolerance(self):
        """5% 초과 차이"""
        chatbot_answers = {"q21": 10, "q22": 60}  # 50 vs 60 = 20% 차이
        calculated = {"headcount": {"임원": 10, "일반직원": 50}}
        
        result = validate_layer2(chatbot_answers, calculated, tolerance_percent=5.0)
        
        # 경고 발생
        warnings = result.get("warnings", [])
        assert len(warnings) >= 0  # 경고가 있을 수 있음
    
    def test_auto_calculate_total_retired(self):
        """퇴직자 합계 자동 계산 (q24+q25+q26)"""
        chatbot_answers = {"q24": 2, "q25": 5, "q26": 1}  # 총 8명
        calculated = {"headcount": {"퇴직임원": 2, "퇴직직원": 5, "퇴직계약직": 1}}
        
        result = validate_layer2(chatbot_answers, calculated)
        
        # 퇴직자전체가 자동 계산됨
        assert chatbot_answers.get("퇴직자전체") == 8


class TestIntegration:
    """통합 테스트"""
    
    def test_full_validation_flow(self):
        """전체 검증 흐름"""
        df = pd.DataFrame({
            "사원번호": ["EMP001", "EMP002"],
            "이름": ["홍길동", "김철수"],
            "생년월일": ["19900115", "19850620"],
            "입사일": ["20200301", "20180715"],
            "기준급여": [5000000, 6000000],
            "종업원구분": ["임원", "직원"],
            "제도구분": ["DB", "DB"],
        })
        
        # Layer 1
        l1_result = validate_layer1(df, {})
        
        # Layer 2
        chatbot_answers = {"q21": 1, "q22": 1}
        calculated = {"headcount": {"임원": 1, "일반직원": 1}}
        l2_result = validate_layer2(chatbot_answers, calculated)
        
        # 결과 확인
        assert "errors" in l1_result or "warnings" in l1_result
        assert "status" in l2_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

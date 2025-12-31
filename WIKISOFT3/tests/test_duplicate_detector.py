"""
중복 탐지 모듈 테스트
"""
import pytest
import pandas as pd
from internal.validators.duplicate_detector import (
    detect_duplicates,
    get_duplicate_summary_for_report
)


class TestDuplicateDetection:
    """중복 탐지 테스트"""
    
    def test_no_duplicates(self):
        """중복 없는 케이스"""
        data = [
            ['EMP001', '홍길동', '19900101'],
            ['EMP002', '김철수', '19850515'],
            ['EMP003', '박영희', '19920320'],
        ]
        df = pd.DataFrame(data, columns=['사원번호', '이름', '생년월일'])
        matches = [
            {'source': '사원번호', 'target': '사원번호'},
            {'source': '이름', 'target': '이름'},
            {'source': '생년월일', 'target': '생년월일'},
        ]
        
        result = detect_duplicates(df, df.columns.tolist(), matches)
        
        assert result['has_duplicates'] is False
        assert result['total_duplicates'] == 0
        assert result['summary'] == "중복 없음"
    
    def test_exact_duplicate(self):
        """완전 중복 (사원번호 동일)"""
        data = [
            ['EMP001', '홍길동', '19900101'],
            ['EMP002', '김철수', '19850515'],
            ['EMP001', '홍길동', '19900101'],  # 중복
        ]
        df = pd.DataFrame(data, columns=['사원번호', '이름', '생년월일'])
        matches = [
            {'source': '사원번호', 'target': '사원번호'},
            {'source': '이름', 'target': '이름'},
            {'source': '생년월일', 'target': '생년월일'},
        ]
        
        result = detect_duplicates(df, df.columns.tolist(), matches)
        
        assert result['has_duplicates'] is True
        assert len(result['exact_duplicates']) == 1
        assert result['exact_duplicates'][0]['key'] == 'EMP001'
        assert result['exact_duplicates'][0]['severity'] == 'error'
    
    def test_similar_duplicate(self):
        """유사 중복 (이름+생년월일 동일, 사원번호 다름)"""
        data = [
            ['EMP001', '홍길동', '19900101'],
            ['EMP002', '홍길동', '19900101'],  # 같은 이름+생일, 다른 사번
            ['EMP003', '박영희', '19920320'],
        ]
        df = pd.DataFrame(data, columns=['사원번호', '이름', '생년월일'])
        matches = [
            {'source': '사원번호', 'target': '사원번호'},
            {'source': '이름', 'target': '이름'},
            {'source': '생년월일', 'target': '생년월일'},
        ]
        
        result = detect_duplicates(df, df.columns.tolist(), matches)
        
        assert result['has_duplicates'] is True
        assert len(result['similar_duplicates']) == 1
        assert result['similar_duplicates'][0]['severity'] == 'warning'
        assert 'EMP001' in result['similar_duplicates'][0]['emp_ids']
        assert 'EMP002' in result['similar_duplicates'][0]['emp_ids']
    
    def test_suspicious_duplicate_phone(self):
        """의심 중복 (전화번호 동일)"""
        data = [
            ['EMP001', '홍길동', '01012341234'],
            ['EMP002', '김철수', '01012341234'],  # 같은 전화번호
            ['EMP003', '박영희', '01099998888'],
        ]
        df = pd.DataFrame(data, columns=['사원번호', '이름', '전화번호'])
        matches = [
            {'source': '사원번호', 'target': '사원번호'},
            {'source': '이름', 'target': '이름'},
            {'source': '전화번호', 'target': '전화번호'},
        ]
        
        result = detect_duplicates(df, df.columns.tolist(), matches)
        
        assert result['has_duplicates'] is True
        assert len(result['suspicious_duplicates']) == 1
        assert result['suspicious_duplicates'][0]['key'] == '01012341234'
        assert result['suspicious_duplicates'][0]['severity'] == 'info'
    
    def test_multiple_duplicates(self):
        """여러 종류 중복 동시 발생"""
        data = [
            ['EMP001', '홍길동', '19900101', '01012341234'],
            ['EMP002', '김철수', '19850515', '01055556666'],
            ['EMP001', '홍길동', '19900101', '01012341234'],  # 완전 중복
            ['EMP003', '홍길동', '19900101', '01099998888'],  # 유사 중복
            ['EMP004', '박영희', '19920320', '01055556666'],  # 전화번호 중복
        ]
        df = pd.DataFrame(data, columns=['사원번호', '이름', '생년월일', '전화번호'])
        matches = [
            {'source': '사원번호', 'target': '사원번호'},
            {'source': '이름', 'target': '이름'},
            {'source': '생년월일', 'target': '생년월일'},
            {'source': '전화번호', 'target': '전화번호'},
        ]
        
        result = detect_duplicates(df, df.columns.tolist(), matches)
        
        assert result['has_duplicates'] is True
        assert result['total_duplicates'] == 3
        assert len(result['exact_duplicates']) == 1
        assert len(result['similar_duplicates']) == 1
        assert len(result['suspicious_duplicates']) == 1
    
    def test_empty_dataframe(self):
        """빈 데이터"""
        df = pd.DataFrame()
        result = detect_duplicates(df, [], [])
        
        assert result['has_duplicates'] is False
        assert result['total_duplicates'] == 0
    
    def test_report_summary(self):
        """리포트 요약 생성"""
        duplicates = {
            'exact_duplicates': [
                {'message': '사원번호 중복', 'rows': [0, 2]}
            ],
            'similar_duplicates': [
                {'message': '이름+생일 중복', 'rows': [1, 3]}
            ],
            'suspicious_duplicates': []
        }
        
        items = get_duplicate_summary_for_report(duplicates)
        
        assert len(items) == 2
        assert items[0]['severity'] == 'error'
        assert items[1]['severity'] == 'warning'

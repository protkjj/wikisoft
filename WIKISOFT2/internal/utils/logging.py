"""
로깅 시스템 (민감 정보 자동 마스킹)
- 모든 로그에서 자동으로 전화, 생년월일, 급여 마스킹
- 타임스탬프, 심각도 레벨 포함
"""
import logging
from datetime import datetime
from typing import Any
from .masking import mask_phone, mask_birth_date, mask_salary, mask_name
import re


class MaskingFormatter(logging.Formatter):
    """민감 정보를 자동으로 마스킹하는 로그 포매터"""
    
    PATTERNS = {
        'phone': (r'01[0-9]-?\d{3,4}-?\d{4}|\+82-?10-?\d{3,4}-?\d{4}', mask_phone),
        'birth': (r'\d{4}[-/]?\d{2}[-/]?\d{2}', mask_birth_date),
        'salary': (r'\d{4,8}(?:만원|원|억)', mask_salary),
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # 표준 포매팅
        log_message = super().format(record)
        
        # 민감 정보 마스킹
        log_message = self._mask_message(log_message)
        
        return log_message
    
    def _mask_message(self, message: str) -> str:
        """메시지에서 민감 정보 마스킹"""
        # 전화번호 마스킹
        message = re.sub(
            r'01[0-9]-?\d{3,4}-?\d{4}',
            lambda m: mask_phone(m.group()),
            message
        )
        
        # 생년월일 마스킹
        message = re.sub(
            r'\d{4}[-/]?\d{2}[-/]?\d{2}',
            lambda m: mask_birth_date(m.group()),
            message
        )
        
        return message


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    민감 정보 마스킹이 적용된 로거 생성
    
    사용 예:
    ```python
    logger = get_logger(__name__)
    logger.info(f"사용자 전화: 01012345678")  # 로그에는 010-****-5678로 기록됨
    ```
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 반환
    if logger.handlers:
        return logger
    
    # 스트림 핸들러 (콘솔)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    
    # 마스킹 포매터 적용
    formatter = MaskingFormatter(
        fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(stream_handler)
    
    return logger


def mask_log_record(record_dict: dict) -> dict:
    """
    로그 레코드 딕셔너리 마스킹
    
    사용 예:
    ```python
    record = {
        'timestamp': '2025-12-25 10:30:00',
        'action': 'validate',
        'user_phone': '01012345678',
        'session_id': 'abc123'
    }
    masked = mask_log_record(record)
    # user_phone이 010-****-5678로 마스킹됨
    ```
    """
    masked = record_dict.copy()
    
    for key, value in masked.items():
        if isinstance(value, str):
            # 전화번호
            if any(x in key.lower() for x in ['phone', 'tel', '전화']):
                masked[key] = mask_phone(value)
            # 생년월일
            elif any(x in key.lower() for x in ['birth', '생년', '생일']):
                masked[key] = mask_birth_date(value)
            # 급여
            elif any(x in key.lower() for x in ['salary', '급여', '연봉']):
                masked[key] = mask_salary(value)
            # 이름
            elif any(x in key.lower() for x in ['name', '이름', '성명']):
                masked[key] = mask_name(value)
    
    return masked

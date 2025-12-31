"""
보안 유틸리티 모듈

- 파일 업로드 검증
- 개인정보 마스킹
- Rate Limiting 헬퍼
"""

import re
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status


# ============================================================
# 파일 업로드 검증
# ============================================================

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

# 허용된 MIME 타입
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
    'application/vnd.ms-excel',  # xls
    'text/csv',
    'application/csv',
    'application/octet-stream',  # 일부 브라우저에서 사용
}

# 최대 파일 크기 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 최대 행 수 (DoS 방지)
MAX_ROW_COUNT = 100_000


async def validate_upload_file(file: UploadFile) -> Tuple[bytes, str]:
    """
    업로드된 파일 검증.
    
    Args:
        file: FastAPI UploadFile
    
    Returns:
        (파일 바이트, 파일명)
    
    Raises:
        HTTPException: 검증 실패 시
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일이 필요합니다."
        )
    
    # 1. 확장자 검증
    filename = file.filename.lower()
    ext = '.' + filename.rsplit('.', 1)[-1] if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"허용되지 않은 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 2. MIME 타입 검증 (있는 경우)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        # 경고만 (일부 브라우저는 잘못된 MIME 타입을 보냄)
        pass
    
    # 3. 파일 크기 검증
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기가 너무 큽니다. 최대: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일입니다."
        )
    
    # 4. 매직 바이트 검증 (파일 시그니처)
    if not _validate_magic_bytes(file_bytes, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 내용이 확장자와 일치하지 않습니다."
        )
    
    return file_bytes, file.filename


def _validate_magic_bytes(data: bytes, ext: str) -> bool:
    """파일 매직 바이트(시그니처) 검증."""
    if len(data) < 4:
        return False
    
    # XLSX (ZIP 기반)
    if ext == '.xlsx':
        return data[:4] == b'PK\x03\x04'
    
    # XLS (OLE2)
    if ext == '.xls':
        return data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    
    # CSV (텍스트)
    if ext == '.csv':
        try:
            # 첫 1000바이트가 텍스트인지 확인
            data[:1000].decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                data[:1000].decode('cp949')
                return True
            except UnicodeDecodeError:
                return False
    
    return True


# ============================================================
# 개인정보 마스킹
# ============================================================

# 마스킹 패턴
PATTERNS = {
    'phone': re.compile(r'01[0-9]-?\d{3,4}-?\d{4}'),
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'ssn': re.compile(r'\d{6}-?[1-4]\d{6}'),  # 주민등록번호
    'emp_id': re.compile(r'(EMP|emp|사원)?-?\d{4,10}'),  # 사원번호
    'salary': re.compile(r'\d{1,3}(,\d{3}){2,}'),  # 급여 (백만원 이상)
}


def mask_sensitive_data(text: str, mask_char: str = '*') -> str:
    """
    텍스트에서 민감한 개인정보 마스킹.
    
    Args:
        text: 원본 텍스트
        mask_char: 마스킹 문자
    
    Returns:
        마스킹된 텍스트
    """
    if not text or not isinstance(text, str):
        return text
    
    result = text
    
    # 주민등록번호 (전체 마스킹)
    result = PATTERNS['ssn'].sub(lambda m: mask_char * len(m.group()), result)
    
    # 전화번호 (중간 마스킹)
    def mask_phone(m):
        phone = m.group()
        if len(phone) >= 10:
            return phone[:3] + mask_char * 4 + phone[-4:]
        return mask_char * len(phone)
    result = PATTERNS['phone'].sub(mask_phone, result)
    
    # 이메일 (부분 마스킹)
    def mask_email(m):
        email = m.group()
        local, domain = email.split('@')
        if len(local) > 2:
            masked_local = local[0] + mask_char * (len(local) - 2) + local[-1]
        else:
            masked_local = mask_char * len(local)
        return f"{masked_local}@{domain}"
    result = PATTERNS['email'].sub(mask_email, result)
    
    return result


def mask_pii_in_message(message: str, mask_char: str = '*') -> str:
    """
    에러/경고 메시지에서 개인정보 마스킹.
    사원번호, 생년월일, 기준급여 등을 마스킹.
    
    Args:
        message: 원본 메시지
        mask_char: 마스킹 문자
    
    Returns:
        마스킹된 메시지
    """
    if not message or not isinstance(message, str):
        return message
    
    result = message
    
    # 사원번호 패턴 (숫자 6자리 이상)
    result = re.sub(
        r'(사원번호[:\s]*)[0-9]{6,}',
        lambda m: m.group(1) + mask_char * 6 + '...',
        result
    )
    
    # 생년월일 패턴 (YYYYMMDD 또는 YYYY-MM-DD)
    result = re.sub(
        r'(생년월일[:\s]*)(\d{4}[-/]?\d{2}[-/]?\d{2}|\d{8}\.?\d*)',
        lambda m: m.group(1) + '****-**-**',
        result
    )
    
    # 입사일 패턴
    result = re.sub(
        r'(입사일[자]?[:\s]*)(\d{4}[-/]?\d{2}[-/]?\d{2}|\d+\.?\d*)',
        lambda m: m.group(1) + '****-**-**',
        result
    )
    
    # 급여 금액 (큰 숫자)
    result = re.sub(
        r'(기준급여[:\s]*)[\d,]+\.?\d*',
        lambda m: m.group(1) + '*,***,***',
        result
    )
    
    # 퇴직금추계액
    result = re.sub(
        r'(퇴직금추계액[:\s]*)[\d,]+\.?\d*',
        lambda m: m.group(1) + '*,***,***',
        result
    )
    
    return result


def mask_anomaly_messages(anomalies: dict) -> dict:
    """
    anomalies 딕셔너리의 모든 메시지 마스킹.
    """
    if not anomalies:
        return anomalies
    
    result = anomalies.copy()
    
    if 'anomalies' in result:
        masked_anomalies = []
        for a in result['anomalies']:
            masked = a.copy()
            if 'message' in masked:
                masked['message'] = mask_pii_in_message(masked['message'])
            if 'auto_fix' in masked:
                masked['auto_fix'] = mask_pii_in_message(masked['auto_fix'])
            masked_anomalies.append(masked)
        result['anomalies'] = masked_anomalies
    
    return result


def mask_dict_values(data: dict, fields_to_mask: set = None) -> dict:
    """
    딕셔너리의 특정 필드 값 마스킹.
    
    Args:
        data: 원본 딕셔너리
        fields_to_mask: 마스킹할 필드명 집합 (None이면 자동 감지)
    
    Returns:
        마스킹된 딕셔너리
    """
    if not data:
        return data
    
    # 기본 마스킹 필드
    default_fields = {
        '이름', '성명', 'name', '전화번호', 'phone', '휴대폰',
        '이메일', 'email', '주민등록번호', 'ssn', '주소', 'address'
    }
    fields = fields_to_mask or default_fields
    
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = mask_dict_values(value, fields)
        elif isinstance(value, list):
            result[key] = [
                mask_dict_values(item, fields) if isinstance(item, dict)
                else mask_sensitive_data(str(item)) if key.lower() in {f.lower() for f in fields}
                else item
                for item in value
            ]
        elif key.lower() in {f.lower() for f in fields}:
            result[key] = mask_sensitive_data(str(value)) if value else value
        else:
            result[key] = value
    
    return result


# ============================================================
# 보안 로거
# ============================================================

class SecureLogger:
    """개인정보 마스킹이 적용된 로거."""
    
    def __init__(self, name: str = "wikisoft"):
        import logging
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _mask(self, msg: str) -> str:
        return mask_sensitive_data(str(msg))
    
    def info(self, msg: str, *args):
        self.logger.info(self._mask(msg), *args)
    
    def warning(self, msg: str, *args):
        self.logger.warning(self._mask(msg), *args)
    
    def error(self, msg: str, *args):
        self.logger.error(self._mask(msg), *args)
    
    def debug(self, msg: str, *args):
        self.logger.debug(self._mask(msg), *args)


# 글로벌 보안 로거
secure_logger = SecureLogger()

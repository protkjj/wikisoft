"""
PII Detection Module

Automatically detect personally identifiable information in text and data.
"""

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel


class PIIType(str, Enum):
    """Types of PII that can be detected."""

    # Korean-specific
    SSN = "ssn"                    # 주민등록번호
    PHONE_KR = "phone_kr"          # 한국 전화번호
    CARD_NUMBER = "card_number"    # 카드번호

    # Universal
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    BIRTH_DATE = "birth_date"
    BANK_ACCOUNT = "bank_account"

    # Custom patterns
    EMPLOYEE_ID = "employee_id"


class PIIMatch(BaseModel):
    """A detected PII match."""

    pii_type: PIIType
    value: str
    masked_value: str
    start: int
    end: int
    confidence: float  # 0.0 to 1.0
    field_name: str | None = None
    row_index: int | None = None


# Korean SSN pattern: 6 digits - 7 digits
SSN_PATTERN = re.compile(r'\d{6}[-\s]?\d{7}')

# Korean phone patterns
PHONE_KR_PATTERNS = [
    re.compile(r'01[016789][-\s]?\d{3,4}[-\s]?\d{4}'),  # Mobile
    re.compile(r'0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}'),     # Landline
]

# Email pattern
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Card number pattern (16 digits with optional separators)
CARD_PATTERN = re.compile(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}')

# Bank account patterns (Korean banks)
BANK_ACCOUNT_PATTERNS = [
    re.compile(r'\d{3,4}[-\s]?\d{2,4}[-\s]?\d{4,6}'),
]

# Date patterns for birth dates
DATE_PATTERNS = [
    re.compile(r'\d{4}[-./]\d{2}[-./]\d{2}'),  # YYYY-MM-DD
    re.compile(r'\d{2}[-./]\d{2}[-./]\d{4}'),  # DD-MM-YYYY
    re.compile(r'\d{8}'),                       # YYYYMMDD
]

# Korean name pattern (2-4 Korean characters)
KOREAN_NAME_PATTERN = re.compile(r'[가-힣]{2,4}')


def _mask_ssn(value: str) -> str:
    """Mask SSN: 850101-1234567 → 850101-*******"""
    clean = re.sub(r'[-\s]', '', value)
    return f"{clean[:6]}-*******"


def _mask_phone(value: str) -> str:
    """Mask phone: 010-1234-5678 → 010-****-5678"""
    clean = re.sub(r'[-\s]', '', value)
    if len(clean) == 11:
        return f"{clean[:3]}-****-{clean[-4:]}"
    elif len(clean) == 10:
        return f"{clean[:3]}-***-{clean[-4:]}"
    return clean[:3] + "*" * (len(clean) - 7) + clean[-4:]


def _mask_email(value: str) -> str:
    """Mask email: test@example.com → t***@example.com"""
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    if len(local) <= 1:
        masked = "*"
    else:
        masked = local[0] + "*" * (len(local) - 1)
    return f"{masked}@{domain}"


def _mask_card(value: str) -> str:
    """Mask card: 1234-5678-9012-3456 → 1234-****-****-3456"""
    clean = re.sub(r'[-\s]', '', value)
    return f"{clean[:4]}-****-****-{clean[-4:]}"


def _mask_name(value: str) -> str:
    """Mask Korean name: 김철수 → 김*수"""
    if len(value) == 2:
        return value[0] + "*"
    elif len(value) >= 3:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return "*"


def detect_pii(value: str, field_name: str | None = None) -> list[PIIMatch]:
    """
    Detect PII in a single value.

    Args:
        value: Text to scan for PII
        field_name: Optional field name for context

    Returns:
        List of PII matches found
    """
    if not value or not isinstance(value, str):
        return []

    matches: list[PIIMatch] = []

    # SSN detection
    for match in SSN_PATTERN.finditer(value):
        matches.append(PIIMatch(
            pii_type=PIIType.SSN,
            value=match.group(),
            masked_value=_mask_ssn(match.group()),
            start=match.start(),
            end=match.end(),
            confidence=0.95,
            field_name=field_name,
        ))

    # Phone detection
    for pattern in PHONE_KR_PATTERNS:
        for match in pattern.finditer(value):
            # Avoid duplicate with SSN
            if any(m.start <= match.start() < m.end for m in matches):
                continue
            matches.append(PIIMatch(
                pii_type=PIIType.PHONE_KR,
                value=match.group(),
                masked_value=_mask_phone(match.group()),
                start=match.start(),
                end=match.end(),
                confidence=0.9,
                field_name=field_name,
            ))

    # Email detection
    for match in EMAIL_PATTERN.finditer(value):
        matches.append(PIIMatch(
            pii_type=PIIType.EMAIL,
            value=match.group(),
            masked_value=_mask_email(match.group()),
            start=match.start(),
            end=match.end(),
            confidence=0.95,
            field_name=field_name,
        ))

    # Card number detection
    for match in CARD_PATTERN.finditer(value):
        matches.append(PIIMatch(
            pii_type=PIIType.CARD_NUMBER,
            value=match.group(),
            masked_value=_mask_card(match.group()),
            start=match.start(),
            end=match.end(),
            confidence=0.85,
            field_name=field_name,
        ))

    return matches


def detect_pii_in_dataframe(
    data: list[dict[str, Any]],
    sensitive_fields: list[str] | None = None,
) -> dict[str, list[PIIMatch]]:
    """
    Detect PII in a list of dictionaries (DataFrame-like structure).

    Args:
        data: List of row dictionaries
        sensitive_fields: Optional list of fields to scan (scans all if None)

    Returns:
        Dictionary mapping field names to list of PII matches
    """
    results: dict[str, list[PIIMatch]] = {}

    if not data:
        return results

    # Get all field names if not specified
    if sensitive_fields is None:
        sensitive_fields = list(data[0].keys())

    for row_idx, row in enumerate(data):
        for field in sensitive_fields:
            value = row.get(field)
            if value is None:
                continue

            matches = detect_pii(str(value), field_name=field)
            for match in matches:
                match.row_index = row_idx

            if matches:
                if field not in results:
                    results[field] = []
                results[field].extend(matches)

    return results


def scan_text_for_pii(text: str) -> list[PIIMatch]:
    """
    Scan free-form text for PII.

    This is useful for scanning documents, notes, or unstructured data.

    Args:
        text: Text to scan

    Returns:
        List of PII matches found
    """
    return detect_pii(text)


def get_pii_field_suggestions(field_name: str) -> list[PIIType]:
    """
    Suggest likely PII types based on field name.

    Args:
        field_name: Name of the field

    Returns:
        List of likely PII types
    """
    field_lower = field_name.lower()

    suggestions = []

    # Korean field name patterns
    if any(kw in field_lower for kw in ['주민', 'ssn', 'resident']):
        suggestions.append(PIIType.SSN)
    if any(kw in field_lower for kw in ['전화', 'phone', 'tel', '연락처', '휴대폰', 'mobile']):
        suggestions.append(PIIType.PHONE_KR)
    if any(kw in field_lower for kw in ['이메일', 'email', 'mail']):
        suggestions.append(PIIType.EMAIL)
    if any(kw in field_lower for kw in ['이름', 'name', '성명']):
        suggestions.append(PIIType.NAME)
    if any(kw in field_lower for kw in ['주소', 'address', 'addr']):
        suggestions.append(PIIType.ADDRESS)
    if any(kw in field_lower for kw in ['생년월일', 'birth', 'birthday', '생일']):
        suggestions.append(PIIType.BIRTH_DATE)
    if any(kw in field_lower for kw in ['카드', 'card']):
        suggestions.append(PIIType.CARD_NUMBER)
    if any(kw in field_lower for kw in ['계좌', 'account', 'bank']):
        suggestions.append(PIIType.BANK_ACCOUNT)

    return suggestions

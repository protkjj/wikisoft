"""
Data Masking Module

Mask PII while preserving data utility for analysis.
"""

import re
from typing import Any

from .detector import PIIType, detect_pii


def mask_value(value: str, pii_type: PIIType | None = None) -> str:
    """
    Mask a value based on its PII type.

    If pii_type is not specified, attempts to auto-detect.

    Args:
        value: Value to mask
        pii_type: Type of PII (optional, will auto-detect if not provided)

    Returns:
        Masked value
    """
    if not value or not isinstance(value, str):
        return value

    # Auto-detect if type not specified
    if pii_type is None:
        matches = detect_pii(value)
        if matches:
            return matches[0].masked_value
        return value

    # Apply specific masking based on type
    maskers = {
        PIIType.SSN: mask_ssn,
        PIIType.PHONE_KR: mask_phone,
        PIIType.PHONE: mask_phone,
        PIIType.EMAIL: mask_email,
        PIIType.NAME: mask_name,
        PIIType.CARD_NUMBER: _mask_card,
        PIIType.BANK_ACCOUNT: _mask_bank_account,
        PIIType.BIRTH_DATE: mask_birth_date,
        PIIType.ADDRESS: mask_address,
    }

    masker = maskers.get(pii_type)
    if masker:
        return masker(value)

    return value


def mask_name(name: str) -> str:
    """
    Mask a Korean or English name.

    Examples:
        김철수 → 김*수
        홍길동 → 홍*동
        John Smith → J*** S****

    Args:
        name: Name to mask

    Returns:
        Masked name
    """
    if not name:
        return name

    # Check if Korean name
    if re.match(r'^[가-힣]+$', name):
        if len(name) == 2:
            return name[0] + "*"
        elif len(name) >= 3:
            return name[0] + "*" * (len(name) - 2) + name[-1]
        return "*"

    # English name (first last)
    parts = name.split()
    if len(parts) >= 2:
        masked_parts = []
        for part in parts:
            if len(part) <= 1:
                masked_parts.append("*")
            else:
                masked_parts.append(part[0] + "*" * (len(part) - 1))
        return " ".join(masked_parts)

    # Single word name
    if len(name) <= 1:
        return "*"
    return name[0] + "*" * (len(name) - 1)


def mask_phone(phone: str) -> str:
    """
    Mask a phone number.

    Examples:
        010-1234-5678 → 010-****-5678
        02-123-4567 → 02-***-4567

    Args:
        phone: Phone number to mask

    Returns:
        Masked phone number
    """
    if not phone:
        return phone

    # Remove separators for processing
    clean = re.sub(r'[-\s()]', '', phone)

    if len(clean) == 11:  # Mobile: 01012345678
        return f"{clean[:3]}-****-{clean[-4:]}"
    elif len(clean) == 10:  # Landline: 0212345678
        return f"{clean[:2]}-****-{clean[-4:]}"
    elif len(clean) == 9:  # Short landline
        return f"{clean[:2]}-***-{clean[-4:]}"

    # Fallback: mask middle portion
    if len(clean) >= 7:
        return clean[:3] + "*" * (len(clean) - 7) + clean[-4:]

    return "*" * len(clean)


def mask_email(email: str) -> str:
    """
    Mask an email address.

    Examples:
        test@example.com → t***@example.com
        user123@domain.co.kr → u******@domain.co.kr

    Args:
        email: Email to mask

    Returns:
        Masked email
    """
    if not email or "@" not in email:
        return email

    local, domain = email.split("@", 1)

    if len(local) <= 1:
        masked_local = "*"
    elif len(local) <= 3:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def mask_ssn(ssn: str) -> str:
    """
    Mask a Korean SSN (주민등록번호).

    Examples:
        850101-1234567 → 850101-*******
        8501011234567 → 850101-*******

    Args:
        ssn: SSN to mask

    Returns:
        Masked SSN
    """
    if not ssn:
        return ssn

    clean = re.sub(r'[-\s]', '', ssn)

    if len(clean) >= 13:
        return f"{clean[:6]}-*******"

    return "*" * len(clean)


def _mask_card(card: str) -> str:
    """Mask a credit card number."""
    clean = re.sub(r'[-\s]', '', card)
    if len(clean) >= 16:
        return f"{clean[:4]}-****-****-{clean[-4:]}"
    return "*" * len(clean)


def _mask_bank_account(account: str) -> str:
    """Mask a bank account number."""
    clean = re.sub(r'[-\s]', '', account)
    if len(clean) >= 8:
        return clean[:3] + "*" * (len(clean) - 6) + clean[-3:]
    return "*" * len(clean)


def mask_birth_date(date: str, format_type: str = "year_only") -> str:
    """
    Mask a birth date.

    Args:
        date: Date string to mask
        format_type: "year_only" shows only year, "decade" shows decade

    Returns:
        Masked date
    """
    if not date:
        return date

    # Try to extract year
    year_match = re.search(r'(19|20)\d{2}', date)
    if year_match:
        year = year_match.group()
        if format_type == "year_only":
            return f"{year}-**-**"
        elif format_type == "decade":
            decade = year[:3] + "0"
            return f"{decade}년대"

    return "****-**-**"


def mask_address(address: str) -> str:
    """
    Mask an address, keeping only city/district level.

    Examples:
        서울시 강남구 테헤란로 123 → 서울시 강남구 ***

    Args:
        address: Address to mask

    Returns:
        Masked address
    """
    if not address:
        return address

    # Korean address patterns
    # City + District pattern
    pattern = re.compile(r'^(.*?[시도군구])\s*(.*?[구동면읍리로길])?')
    match = pattern.match(address)

    if match:
        city = match.group(1) or ""
        district = match.group(2) or ""
        return f"{city} {district} ***".strip()

    # Fallback: show first portion only
    parts = address.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]} ***"

    return "***"


def mask_dataframe(
    data: list[dict[str, Any]],
    fields_to_mask: dict[str, PIIType] | None = None,
    auto_detect: bool = True,
) -> list[dict[str, Any]]:
    """
    Mask PII in a list of dictionaries (DataFrame-like structure).

    Args:
        data: List of row dictionaries
        fields_to_mask: Dictionary mapping field names to PII types
        auto_detect: If True, auto-detect PII in all string fields

    Returns:
        Data with PII masked
    """
    if not data:
        return data

    result = []

    for row in data:
        masked_row = row.copy()

        for field, value in row.items():
            if value is None or not isinstance(value, str):
                continue

            # Check explicit masking rules
            if fields_to_mask and field in fields_to_mask:
                masked_row[field] = mask_value(value, fields_to_mask[field])
            elif auto_detect:
                # Auto-detect and mask
                matches = detect_pii(str(value))
                if matches:
                    masked_row[field] = matches[0].masked_value

        result.append(masked_row)

    return result

"""
WIKISOFT 4.1 Core Privacy Module

Privacy First - PII detection, masking, and anonymization.

Components:
- detector: Automatic PII detection (주민번호, 전화번호, etc.)
- masker: Data masking (김철수 → 김*수)
- anonymizer: k-anonymity and data anonymization
"""

from .detector import (
    PIIType,
    PIIMatch,
    detect_pii,
    detect_pii_in_dataframe,
    scan_text_for_pii,
)
from .masker import (
    mask_value,
    mask_name,
    mask_phone,
    mask_email,
    mask_ssn,
    mask_dataframe,
)
from .anonymizer import (
    anonymize_field,
    k_anonymize,
    generalize_age,
    generalize_date,
)

__all__ = [
    # Detector
    "PIIType",
    "PIIMatch",
    "detect_pii",
    "detect_pii_in_dataframe",
    "scan_text_for_pii",
    # Masker
    "mask_value",
    "mask_name",
    "mask_phone",
    "mask_email",
    "mask_ssn",
    "mask_dataframe",
    # Anonymizer
    "anonymize_field",
    "k_anonymize",
    "generalize_age",
    "generalize_date",
]

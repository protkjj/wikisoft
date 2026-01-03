"""
Data Anonymization Module

Implements k-anonymity and data generalization for privacy-preserving exports.
"""

import hashlib
from datetime import date, datetime
from typing import Any


def anonymize_field(value: str, salt: str = "") -> str:
    """
    Anonymize a field using one-way hashing.

    The same value with the same salt will always produce the same hash,
    allowing for linkage within a dataset while preventing identification.

    Args:
        value: Value to anonymize
        salt: Optional salt for the hash

    Returns:
        Anonymized (hashed) value
    """
    if not value:
        return value

    combined = f"{salt}{value}".encode('utf-8')
    hash_value = hashlib.sha256(combined).hexdigest()
    return f"ANON_{hash_value[:12]}"


def generalize_age(birth_date: str | date | datetime, bracket_size: int = 10) -> str:
    """
    Generalize age into brackets for k-anonymity.

    Args:
        birth_date: Birth date (string, date, or datetime)
        bracket_size: Size of age brackets (default: 10 years)

    Returns:
        Age bracket string (e.g., "30-39")
    """
    # Parse birth date
    if isinstance(birth_date, str):
        # Try common formats
        for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"]:
            try:
                birth_date = datetime.strptime(birth_date, fmt).date()
                break
            except ValueError:
                continue
        else:
            return "알 수 없음"

    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()

    # Calculate age
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    # Create bracket
    bracket_start = (age // bracket_size) * bracket_size
    bracket_end = bracket_start + bracket_size - 1

    return f"{bracket_start}-{bracket_end}"


def generalize_date(
    date_value: str | date | datetime,
    level: str = "month",
) -> str:
    """
    Generalize a date to reduce precision.

    Args:
        date_value: Date to generalize
        level: Generalization level ("year", "quarter", "month")

    Returns:
        Generalized date string
    """
    # Parse date
    if isinstance(date_value, str):
        for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"]:
            try:
                date_value = datetime.strptime(date_value, fmt).date()
                break
            except ValueError:
                continue
        else:
            return "알 수 없음"

    if isinstance(date_value, datetime):
        date_value = date_value.date()

    if level == "year":
        return f"{date_value.year}"
    elif level == "quarter":
        quarter = (date_value.month - 1) // 3 + 1
        return f"{date_value.year}-Q{quarter}"
    elif level == "month":
        return f"{date_value.year}-{date_value.month:02d}"

    return str(date_value)


def generalize_location(address: str, level: str = "city") -> str:
    """
    Generalize an address to reduce precision.

    Args:
        address: Full address
        level: Generalization level ("city", "district", "region")

    Returns:
        Generalized location
    """
    if not address:
        return "알 수 없음"

    # Korean address parsing
    import re

    # Extract components
    city_match = re.search(r'(서울|부산|대구|인천|광주|대전|울산|세종|[가-힣]+[시도])', address)
    district_match = re.search(r'([가-힣]+[구군])', address)

    if level == "region":
        # Just major region
        if city_match:
            city = city_match.group(1)
            if city in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종"]:
                return city
            return city.rstrip("시도")
        return "기타"

    elif level == "city":
        if city_match:
            return city_match.group(1)
        return "알 수 없음"

    elif level == "district":
        parts = []
        if city_match:
            parts.append(city_match.group(1))
        if district_match:
            parts.append(district_match.group(1))
        return " ".join(parts) if parts else "알 수 없음"

    return address


def k_anonymize(
    data: list[dict[str, Any]],
    quasi_identifiers: list[str],
    k: int = 5,
    generalizers: dict[str, callable] | None = None,
) -> list[dict[str, Any]]:
    """
    Apply k-anonymity to a dataset.

    k-anonymity ensures that each record is indistinguishable from at least
    k-1 other records with respect to quasi-identifiers.

    Args:
        data: List of row dictionaries
        quasi_identifiers: Fields that could identify individuals when combined
        k: Minimum group size (default: 5)
        generalizers: Custom generalization functions for each field

    Returns:
        Anonymized data satisfying k-anonymity
    """
    if not data:
        return data

    # Default generalizers
    default_generalizers = {
        "age": lambda x: generalize_age(x, bracket_size=10),
        "birth_date": lambda x: generalize_date(x, level="year"),
        "생년월일": lambda x: generalize_date(x, level="year"),
        "address": lambda x: generalize_location(x, level="city"),
        "주소": lambda x: generalize_location(x, level="city"),
        "hire_date": lambda x: generalize_date(x, level="quarter"),
        "입사일자": lambda x: generalize_date(x, level="quarter"),
    }

    if generalizers:
        default_generalizers.update(generalizers)

    # First pass: apply generalizations
    generalized_data = []
    for row in data:
        new_row = row.copy()
        for field in quasi_identifiers:
            if field in new_row and new_row[field] is not None:
                generalizer = default_generalizers.get(field.lower())
                if generalizer:
                    new_row[field] = generalizer(str(new_row[field]))
        generalized_data.append(new_row)

    # Second pass: check k-anonymity and suppress if needed
    # Group by quasi-identifier values
    from collections import Counter

    def get_qi_tuple(row):
        return tuple(str(row.get(qi, "")) for qi in quasi_identifiers)

    qi_counts = Counter(get_qi_tuple(row) for row in generalized_data)

    # Mark groups smaller than k for suppression
    small_groups = {qi for qi, count in qi_counts.items() if count < k}

    result = []
    for row in generalized_data:
        qi_tuple = get_qi_tuple(row)
        if qi_tuple in small_groups:
            # Suppress quasi-identifiers for small groups
            suppressed_row = row.copy()
            for qi in quasi_identifiers:
                suppressed_row[qi] = "*"
            result.append(suppressed_row)
        else:
            result.append(row)

    return result


def calculate_information_loss(
    original_data: list[dict[str, Any]],
    anonymized_data: list[dict[str, Any]],
    fields: list[str],
) -> float:
    """
    Calculate information loss after anonymization.

    Args:
        original_data: Original dataset
        anonymized_data: Anonymized dataset
        fields: Fields to compare

    Returns:
        Information loss ratio (0.0 to 1.0)
    """
    if not original_data or not anonymized_data:
        return 0.0

    total_fields = len(original_data) * len(fields)
    changed_fields = 0

    for orig, anon in zip(original_data, anonymized_data):
        for field in fields:
            orig_val = str(orig.get(field, ""))
            anon_val = str(anon.get(field, ""))
            if orig_val != anon_val:
                changed_fields += 1

    return changed_fields / total_fields if total_fields > 0 else 0.0

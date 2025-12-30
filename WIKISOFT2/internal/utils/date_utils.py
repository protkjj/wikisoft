import re
from datetime import datetime, timedelta
from typing import Optional, Union

import pandas as pd


def _excel_serial_to_datetime(value: Union[int, float]) -> Optional[datetime]:
    """Convert Excel serial date (1900 system) to datetime.
    Excel's day 1 is 1899-12-31 or 1899-12-30 depending on libraries.
    Pandas uses 1899-12-30; we follow that for consistency.
    """
    try:
        days = int(float(value))
        if 10000 > days or days > 80000:
            # Guardrail: likely not a serial date
            return None
        base = datetime(1899, 12, 30)
        return base + timedelta(days=days)
    except Exception:
        return None


def _to_datetime(value: Union[str, int, float, datetime, pd.Timestamp]) -> Optional[datetime]:
    """Best-effort parse into datetime.
    Supports: datetime, pd.Timestamp, yyyymmdd, yyyy-mm-dd, yyyy/mm/dd, yyyy.mm.dd,
    Excel serials, and common free-form digit-only strings.
    """
    if value is None:
        return None

    # Already a datetime-like
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            return pd.Timestamp(value).to_pydatetime()
        except Exception:
            return None

    # Excel serials (int/float)
    if isinstance(value, (int, float)):
        dt = _excel_serial_to_datetime(value)
        if dt:
            return dt
        # If 8-digit integer like 19900515
        s = str(int(value))
        if len(s) == 8:
            try:
                return datetime.strptime(s, "%Y%m%d")
            except Exception:
                return None
        return None

    # Strings
    s = str(value).strip()
    if not s:
        return None

    # If looks like ISO with separators
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass

    # Digit-only normalization
    digits = re.sub(r"\D", "", s)
    if len(digits) == 8:
        try:
            return datetime.strptime(digits, "%Y%m%d")
        except Exception:
            return None
    if len(digits) == 6:
        # YYMMDD → map century: 00-49 → 2000s, 50-99 → 1900s
        try:
            yy = int(digits[:2])
            century = 2000 if yy <= 49 else 1900
            dt = datetime.strptime(str(century + yy) + digits[2:], "%Y%m%d")
            return dt
        except Exception:
            return None

    # Fallback: pandas parser
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notnull(dt):
            return dt.to_pydatetime()
    except Exception:
        pass

    return None


def normalize_date(value: Union[str, int, float, datetime, pd.Timestamp]) -> Optional[str]:
    """Normalize any date-like input to yyyymmdd string.

    Returns None if cannot be parsed.
    """
    dt = _to_datetime(value)
    if not dt:
        return None
    return dt.strftime("%Y%m%d")


def is_valid_yyyymmdd(s: str) -> bool:
    """Validate yyyymmdd string strictly."""
    if not isinstance(s, str):
        return False
    if not re.fullmatch(r"\d{8}", s):
        return False
    try:
        datetime.strptime(s, "%Y%m%d")
        return True
    except Exception:
        return False

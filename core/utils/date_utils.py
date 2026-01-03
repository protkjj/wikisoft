import re
from datetime import datetime, timedelta
from typing import Optional, Union

import pandas as pd


def _excel_serial_to_datetime(value: Union[int, float]) -> Optional[datetime]:
    try:
        days = int(float(value))
        if 10000 > days or days > 80000:
            return None
        base = datetime(1899, 12, 30)
        return base + timedelta(days=days)
    except Exception:
        return None


def _to_datetime(value: Union[str, int, float, datetime, pd.Timestamp]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            return pd.Timestamp(value).to_pydatetime()
        except Exception:
            return None
    if isinstance(value, (int, float)):
        dt = _excel_serial_to_datetime(value)
        if dt:
            return dt
        s = str(int(value))
        if len(s) == 8:
            try:
                return datetime.strptime(s, "%Y%m%d")
            except Exception:
                return None
        return None
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    digits = re.sub(r"\D", "", s)
    if len(digits) == 8:
        try:
            return datetime.strptime(digits, "%Y%m%d")
        except Exception:
            return None
    if len(digits) == 6:
        try:
            yy = int(digits[:2])
            century = 2000 if yy <= 49 else 1900
            return datetime.strptime(str(century + yy) + digits[2:], "%Y%m%d")
        except Exception:
            return None
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notnull(dt):
            return dt.to_pydatetime()
    except Exception:
        pass
    return None


def normalize_date(value: Union[str, int, float, datetime, pd.Timestamp]) -> Optional[str]:
    dt = _to_datetime(value)
    if not dt:
        return None
    return dt.strftime("%Y%m%d")


def is_valid_yyyymmdd(s: str) -> bool:
    if not isinstance(s, str):
        return False
    if not re.fullmatch(r"\d{8}", s):
        return False
    try:
        datetime.strptime(s, "%Y%m%d")
        return True
    except Exception:
        return False

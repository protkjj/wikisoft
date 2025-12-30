from typing import Any, Dict, List, Optional
import csv
import io

import chardet
from openpyxl import load_workbook


def _infer_types(rows: List[List[Any]], sample_rows: int = 200) -> Dict[int, str]:
    """간단한 컬럼 타입 추론(문자/숫자/날짜 후보)."""
    import datetime as _dt

    col_types: Dict[int, str] = {}
    sample = rows[:sample_rows]
    for col_idx in range(max((len(r) for r in sample), default=0)):
        values = [r[col_idx] for r in sample if col_idx < len(r)]
        num_cnt = 0
        date_cnt = 0
        for v in values:
            if isinstance(v, (int, float)):
                num_cnt += 1
            elif isinstance(v, _dt.date):
                date_cnt += 1
            else:
                # 숫자 문자열
                try:
                    float(str(v).replace(",", ""))
                    num_cnt += 1
                except Exception:  # noqa: BLE001
                    pass
        if date_cnt > max(num_cnt, 0):
            col_types[col_idx] = "date"
        elif num_cnt > 0:
            col_types[col_idx] = "number"
        else:
            col_types[col_idx] = "string"
    return col_types


def _parse_csv(text: str) -> Dict[str, Any]:
    reader = csv.reader(io.StringIO(text))
    rows: List[List[str]] = list(reader)
    headers = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else []
    return {
        "headers": headers,
        "rows": data_rows,
        "meta": {
            "parser": "csv",
            "total_rows": len(data_rows),
            "column_types": _infer_types(data_rows),
        },
    }


def _parse_xlsx(file_bytes: bytes, sheet_name: Optional[str] = None, max_rows: int = 5000) -> Dict[str, Any]:
    wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
    rows: List[List[Any]] = []
    headers: List[Any] = []
    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx == 0:
            headers = ["" if c is None else str(c) for c in row]
            continue
        if max_rows and len(rows) >= max_rows:
            break
        rows.append(["" if c is None else c for c in row])
    return {
        "headers": headers,
        "rows": rows,
        "meta": {
            "parser": "xlsx",
            "total_rows_sampled": len(rows),
            "sheet": ws.title,
            "column_types": _infer_types(rows),
            "note": f"capped at {max_rows} rows for streaming",
        },
    }


def _parse_xls(file_bytes: bytes, sheet_name: Optional[str] = None, max_rows: int = 5000) -> Dict[str, Any]:
    """XLS (구버전 Excel) 파싱 - pandas + xlrd 사용."""
    import pandas as pd

    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    target_sheet = sheet_name if sheet_name and sheet_name in xls.sheet_names else xls.sheet_names[0]

    # 재직자 명부 시트 자동 탐색
    for name in xls.sheet_names:
        if "재직자" in name and "명부" in name:
            target_sheet = name
            break

    df = pd.read_excel(xls, sheet_name=target_sheet, header=0, nrows=max_rows)
    headers = [str(c) for c in df.columns.tolist()]
    rows = df.values.tolist()

    return {
        "headers": headers,
        "rows": rows,
        "meta": {
            "parser": "xls",
            "total_rows_sampled": len(rows),
            "sheet": target_sheet,
            "available_sheets": xls.sheet_names,
            "column_types": _infer_types(rows),
            "note": f"capped at {max_rows} rows",
        },
    }


def parse_roster(file_bytes: bytes, sheet_name: Optional[str] = None, max_rows: int = 5000) -> Dict[str, Any]:
    """CSV/xlsx/xls 파서 (스트리밍 샘플 기반).

    - xlsx: read_only 모드로 최대 max_rows 샘플링, 시트 선택 지원.
    - xls: pandas + xlrd로 구버전 Excel 지원.
    - csv: chardet로 인코딩 감지 후 파싱.
    """
    # xlsx는 ZIP(0x50 0x4B) 시그니처
    if file_bytes[:2] == b"PK":
        return _parse_xlsx(file_bytes, sheet_name=sheet_name, max_rows=max_rows)

    # xls는 OLE2 (0xD0 0xCF) 시그니처
    if file_bytes[:2] == b"\xd0\xcf":
        return _parse_xls(file_bytes, sheet_name=sheet_name, max_rows=max_rows)

    # 나머지는 CSV로 시도
    detected = chardet.detect(file_bytes)
    encoding = detected.get("encoding") or "utf-8"
    text = file_bytes.decode(encoding, errors="replace")
    parsed = _parse_csv(text)
    parsed["meta"]["encoding"] = encoding
    return parsed

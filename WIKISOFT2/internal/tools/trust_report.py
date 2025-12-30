import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any

# Ensure project root is on sys.path so `internal` package imports resolve
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from internal.processors.validation_layer1 import validate_layer1


def summarize_validation(result: Dict[str, Any]) -> Dict[str, Any]:
    errors = result.get('errors', [])
    warnings = result.get('warnings', [])
    error_rows = sorted(set(e.get('row') for e in errors if 'row' in e))
    warn_rows = sorted(set(w.get('row') for w in warnings if 'row' in w))
    by_column = {}
    for e in errors:
        col = e.get('column', 'UNKNOWN')
        by_column[col] = by_column.get(col, 0) + 1
    for w in warnings:
        col = w.get('column', 'UNKNOWN')
        by_column[col] = by_column.get(col, 0) + 1
    return {
        'error_count': len(errors),
        'warning_count': len(warnings),
        'error_rows': error_rows,
        'warning_rows': warn_rows,
        'by_column': by_column,
        'errors_sample': errors[:20],
        'warnings_sample': warnings[:20],
    }


def compute_trust_score(df: pd.DataFrame, summary: Dict[str, Any]) -> float:
    total_rows = max(len(df), 1)
    error_rows = len(summary['error_rows'])
    # Base pass rate: rows without any error
    pass_rate = (total_rows - error_rows) / total_rows
    # Penalty for high warning volume
    warning_penalty = min(summary['warning_count'] / max(total_rows, 1) * 0.2, 0.2)
    # Trust score in [0,1]
    score = max(0.0, min(1.0, pass_rate - warning_penalty))
    return round(score, 3)


def run_trust_report(file_path: str, sheet_name: str = "(2-2) 재직자 명부") -> Dict[str, Any]:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    result = validate_layer1(df, diagnostic_answers={})
    summary = summarize_validation(result)
    score = compute_trust_score(df, summary)
    return {
        'sheet': sheet_name,
        'rows': len(df),
        'columns': list(df.columns),
        'error_count': summary['error_count'],
        'warning_count': summary['warning_count'],
        'score': score,
        'by_column': summary['by_column'],
        'errors_sample': summary['errors_sample'],
        'warnings_sample': summary['warnings_sample'],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m internal.tools.trust_report <excel_file_path> [sheet_name]")
        sys.exit(1)
    path = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else "(2-2) 재직자 명부"
    report = run_trust_report(path, sheet)
    from pprint import pprint
    pprint(report)

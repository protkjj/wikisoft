from typing import Any, Dict


def generate_report(validation: Dict[str, Any]) -> Dict[str, Any]:
    """간단한 JSON 리포트 스텁.

    - 추후 Excel 강조/다운로드 등으로 확장 예정.
    """
    return {
        "report_type": "json_stub",
        "summary": {
            "passed": validation.get("passed"),
            "warnings": validation.get("warnings", []),
            "checks": validation.get("checks", []),
        },
    }

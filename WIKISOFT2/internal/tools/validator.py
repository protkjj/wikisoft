"""
Validator Tool: 데이터 검증

책임:
- 필드 검증 (data quality)
- 교차 검증 (consistency)
- 규칙 검증 (business rules)
"""

from typing import Any, Dict, List, Optional
from .registry import Tool, ToolParameter, ToolCategory


class ValidatorTool:
    """데이터 검증 도구"""
    
    @staticmethod
    async def validate_schema(
        data: Dict[str, Any],
        schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        스키마 검증
        
        Args:
            data: 검증할 데이터
            schema: {"field": "type", ...}
        
        Returns:
            {
                "valid": bool,
                "errors": [{"field": "", "error": ""}, ...],
                "warnings": [...],
            }
        """
        errors = []
        warnings = []
        
        for field, expected_type in schema.items():
            if field not in data:
                errors.append({
                    "field": field,
                    "error": f"Missing required field: {field}",
                })
            elif expected_type == "number":
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    errors.append({
                        "field": field,
                        "error": f"Expected number, got {type(data[field]).__name__}",
                    })
            elif expected_type == "date":
                try:
                    from datetime import datetime
                    datetime.fromisoformat(str(data[field]))
                except ValueError:
                    errors.append({
                        "field": field,
                        "error": f"Invalid date format: {data[field]}",
                    })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validated_fields": len(schema),
        }
    
    @staticmethod
    async def validate_cross_fields(
        data: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        필드 간 교차 검증
        
        Args:
            data: 검증할 데이터
            rules: [
                {
                    "name": "rule_name",
                    "fields": ["field1", "field2"],
                    "condition": "sum_equals_total",
                    "tolerance": 0.05,
                }
            ]
        
        Returns:
            {
                "valid": bool,
                "results": {
                    "rule_name": {"passed": bool, "message": str},
                    ...
                }
            }
        """
        results = {}
        
        for rule in rules:
            rule_name = rule.get("name", "unknown")
            try:
                # 간단한 rule 처리
                if rule["condition"] == "sum_equals_total":
                    fields = rule.get("fields", [])
                    tolerance = rule.get("tolerance", 0.0)
                    
                    if len(fields) >= 2:
                        field_sum = sum(
                            float(data.get(f, 0)) for f in fields[:-1]
                        )
                        total = float(data.get(fields[-1], 0))
                        diff = abs(field_sum - total) / max(total, 1)
                        
                        passed = diff <= tolerance
                        results[rule_name] = {
                            "passed": passed,
                            "message": f"Sum: {field_sum}, Total: {total}, Diff: {diff:.2%}",
                        }
                else:
                    results[rule_name] = {
                        "passed": True,
                        "message": "Rule not implemented",
                    }
            except Exception as e:
                results[rule_name] = {
                    "passed": False,
                    "message": str(e),
                }
        
        all_passed = all(r["passed"] for r in results.values())
        
        return {
            "valid": all_passed,
            "results": results,
            "passed_rules": sum(1 for r in results.values() if r["passed"]),
            "total_rules": len(rules),
        }
    
    @staticmethod
    async def validate_business_rules(
        data: Dict[str, Any],
        rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        비즈니스 규칙 검증
        
        Args:
            data: 검증할 데이터
            rules: 비즈니스 규칙들
        
        Returns:
            {
                "valid": bool,
                "violations": [{"rule": "", "severity": "error|warning", "message": ""}, ...],
            }
        """
        violations = []
        
        for rule in rules:
            try:
                # 예: "salary > 0"
                if rule.get("type") == "range_check":
                    field = rule.get("field")
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    value = float(data.get(field, 0))
                    
                    if value < min_val or value > max_val:
                        violations.append({
                            "rule": rule.get("name", "unknown"),
                            "severity": rule.get("severity", "warning"),
                            "message": f"{field} out of range [{min_val}, {max_val}]: {value}",
                        })
            except Exception as e:
                violations.append({
                    "rule": rule.get("name", "unknown"),
                    "severity": "error",
                    "message": str(e),
                })
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "total_violations": len(violations),
        }


def register_validator_tools(registry) -> None:
    """Validator Tool 등록"""
    tool1 = Tool(
        name="validate_schema",
        description="데이터가 정의된 스키마를 따르는지 검증합니다",
        category=ToolCategory.VALIDATOR,
        parameters=[
            ToolParameter("data", "dict", "검증할 데이터", required=True),
            ToolParameter("schema", "dict", "스키마 정의", required=True),
        ],
        execute=ValidatorTool.validate_schema,
        cost={"time": 1.0, "tokens": 300},
    )
    registry.register(tool1)
    
    tool2 = Tool(
        name="validate_cross_fields",
        description="여러 필드 간 교차 검증을 수행합니다",
        category=ToolCategory.VALIDATOR,
        parameters=[
            ToolParameter("data", "dict", "검증할 데이터", required=True),
            ToolParameter("rules", "list", "교차 검증 규칙들", required=True),
        ],
        execute=ValidatorTool.validate_cross_fields,
        cost={"time": 1.5, "tokens": 400},
    )
    registry.register(tool2)
    
    tool3 = Tool(
        name="validate_business_rules",
        description="비즈니스 규칙을 검증합니다",
        category=ToolCategory.VALIDATOR,
        parameters=[
            ToolParameter("data", "dict", "검증할 데이터", required=True),
            ToolParameter("rules", "list", "비즈니스 규칙들", required=True),
        ],
        execute=ValidatorTool.validate_business_rules,
        cost={"time": 1.0, "tokens": 300},
    )
    registry.register(tool3)

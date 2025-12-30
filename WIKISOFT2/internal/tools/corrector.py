"""
Corrector Tool: 데이터 수정/보정

책임:
- 데이터 자동 수정
- 불일치 해결
- 값 보정
"""

from typing import Any, Dict, List, Optional


class CorrectorTool:
    """데이터 수정 도구"""
    
    @staticmethod
    async def auto_fix_typos(
        value: str,
        dictionary: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        타이포 자동 수정
        
        Args:
            value: 수정할 문자열
            dictionary: 올바른 단어들
        
        Returns:
            {
                "original": str,
                "corrected": str,
                "confidence": float,
                "alternatives": [str, ...],
            }
        """
        if not dictionary or not value:
            return {
                "original": value,
                "corrected": value,
                "confidence": 1.0,
                "alternatives": [],
            }
        
        # 간단한 편집거리 기반 매칭
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # 가장 유사한 단어 찾기
        value_lower = value.lower()
        matches = [
            (word, levenshtein_distance(value_lower, word.lower()))
            for word in dictionary
        ]
        matches.sort(key=lambda x: x[1])
        
        best_match = matches[0][0] if matches else value
        distance = matches[0][1] if matches else 0
        confidence = max(0, 1.0 - (distance / len(value)))
        
        alternatives = [m[0] for m in matches[:3] if m[1] > 0]
        
        return {
            "original": value,
            "corrected": best_match,
            "confidence": round(confidence, 3),
            "alternatives": alternatives,
        }
    
    @staticmethod
    async def normalize_number(
        value: Any,
        format_type: str = "integer"
    ) -> Dict[str, Any]:
        """
        숫자 정규화
        
        Args:
            value: 정규화할 값
            format_type: "integer", "float", "percentage"
        
        Returns:
            {
                "original": Any,
                "normalized": float,
                "format_type": str,
                "success": bool,
            }
        """
        try:
            # 문자열 공백 제거
            if isinstance(value, str):
                value_str = value.strip().replace(",", "")
            else:
                value_str = str(value)
            
            # 숫자 변환
            num = float(value_str)
            
            # 포맷별 처리
            if format_type == "integer":
                normalized = int(round(num))
            elif format_type == "percentage":
                if num > 100:
                    normalized = num / 100
                else:
                    normalized = num
            else:  # float
                normalized = num
            
            return {
                "original": value,
                "normalized": normalized,
                "format_type": format_type,
                "success": True,
            }
        except (ValueError, TypeError) as e:
            return {
                "original": value,
                "normalized": None,
                "format_type": format_type,
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    async def resolve_mismatch(
        value1: Any,
        value2: Any,
        rule: str = "average"
    ) -> Dict[str, Any]:
        """
        불일치 해결
        
        Args:
            value1: 첫 번째 값
            value2: 두 번째 값
            rule: "average", "first", "second", "max", "min"
        
        Returns:
            {
                "value1": Any,
                "value2": Any,
                "resolved": Any,
                "rule_applied": str,
                "confidence": float,
            }
        """
        try:
            # 숫자인 경우
            try:
                v1 = float(value1)
                v2 = float(value2)
                
                if rule == "average":
                    resolved = (v1 + v2) / 2
                    confidence = 0.7
                elif rule == "first":
                    resolved = v1
                    confidence = 0.5
                elif rule == "second":
                    resolved = v2
                    confidence = 0.5
                elif rule == "max":
                    resolved = max(v1, v2)
                    confidence = 0.6
                elif rule == "min":
                    resolved = min(v1, v2)
                    confidence = 0.6
                else:
                    resolved = v1
                    confidence = 0.5
            except (ValueError, TypeError):
                # 문자열인 경우
                if value1 == value2:
                    resolved = value1
                    confidence = 1.0
                else:
                    resolved = value1
                    confidence = 0.3
            
            return {
                "value1": value1,
                "value2": value2,
                "resolved": resolved,
                "rule_applied": rule,
                "confidence": confidence,
            }
        except Exception as e:
            return {
                "error": str(e),
                "confidence": 0,
            }


def register_corrector_tools(registry) -> None:
    """Corrector Tool 등록"""
    from .registry import Tool, ToolParameter, ToolCategory
    
    tool1 = Tool(
        name="auto_fix_typos",
        description="텍스트의 타이포를 자동으로 수정합니다",
        category=ToolCategory.CORRECTOR,
        parameters=[
            ToolParameter("value", "str", "수정할 문자열", required=True),
            ToolParameter("dictionary", "list", "올바른 단어들", required=False),
        ],
        execute=CorrectorTool.auto_fix_typos,
        cost={"time": 1.0, "tokens": 300},
    )
    registry.register(tool1)
    
    tool2 = Tool(
        name="normalize_number",
        description="숫자를 정규화합니다 (정수, 실수, 백분율)",
        category=ToolCategory.CORRECTOR,
        parameters=[
            ToolParameter("value", "any", "정규화할 값", required=True),
            ToolParameter("format_type", "str", "포맷 유형 (integer, float, percentage)", required=False, default="float"),
        ],
        execute=CorrectorTool.normalize_number,
        cost={"time": 0.5, "tokens": 150},
    )
    registry.register(tool2)
    
    tool3 = Tool(
        name="resolve_mismatch",
        description="두 값의 불일치를 해결합니다",
        category=ToolCategory.CORRECTOR,
        parameters=[
            ToolParameter("value1", "any", "첫 번째 값", required=True),
            ToolParameter("value2", "any", "두 번째 값", required=True),
            ToolParameter("rule", "str", "해결 규칙 (average, first, second, max, min)", required=False, default="average"),
        ],
        execute=CorrectorTool.resolve_mismatch,
        cost={"time": 0.5, "tokens": 150},
    )
    registry.register(tool3)

"""
Analyzer Tool: 데이터 분석

책임:
- 데이터 통계
- 이상치 탐지
- 패턴 분석
"""

from typing import Any, Dict, List
import statistics


class AnalyzerTool:
    """데이터 분석 도구"""
    
    @staticmethod
    async def calculate_statistics(
        values: List[float]
    ) -> Dict[str, Any]:
        """
        통계 계산
        
        Args:
            values: 숫자 리스트
        
        Returns:
            {
                "count": int,
                "sum": float,
                "mean": float,
                "median": float,
                "std_dev": float,
                "min": float,
                "max": float,
            }
        """
        if not values:
            return {"error": "Empty list"}
        
        try:
            values_float = [float(v) for v in values]
            
            return {
                "count": len(values_float),
                "sum": sum(values_float),
                "mean": statistics.mean(values_float),
                "median": statistics.median(values_float),
                "std_dev": statistics.stdev(values_float) if len(values_float) > 1 else 0,
                "min": min(values_float),
                "max": max(values_float),
                "range": max(values_float) - min(values_float),
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def detect_outliers(
        values: List[float],
        method: str = "iqr",
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        이상치 탐지
        
        Args:
            values: 숫자 리스트
            method: "iqr" (Interquartile Range) or "zscore"
            threshold: 이상치 판단 임계값
        
        Returns:
            {
                "outliers": [{"index": int, "value": float, "score": float}, ...],
                "method": str,
                "threshold": float,
            }
        """
        if not values or len(values) < 3:
            return {"outliers": [], "method": method}
        
        try:
            values_float = [float(v) for v in values]
            
            if method == "iqr":
                sorted_vals = sorted(values_float)
                n = len(sorted_vals)
                q1 = sorted_vals[n // 4]
                q3 = sorted_vals[3 * n // 4]
                iqr = q3 - q1
                
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                
                outliers = [
                    {
                        "index": i,
                        "value": v,
                        "score": abs(v - statistics.mean(values_float)) / (statistics.stdev(values_float) or 1)
                    }
                    for i, v in enumerate(values_float)
                    if v < lower_bound or v > upper_bound
                ]
            
            elif method == "zscore":
                mean = statistics.mean(values_float)
                std = statistics.stdev(values_float) if len(values_float) > 1 else 1
                
                outliers = [
                    {
                        "index": i,
                        "value": v,
                        "score": abs((v - mean) / std) if std > 0 else 0
                    }
                    for i, v in enumerate(values_float)
                    if std > 0 and abs((v - mean) / std) > threshold
                ]
            else:
                return {"error": f"Unknown method: {method}"}
            
            # 스코어 내림차순 정렬
            outliers.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "outliers": outliers,
                "count": len(outliers),
                "method": method,
                "threshold": threshold,
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def analyze_distribution(
        values: List[float],
        bins: int = 10
    ) -> Dict[str, Any]:
        """
        분포 분석
        
        Args:
            values: 숫자 리스트
            bins: 히스토그램 구간 수
        
        Returns:
            {
                "distribution": {
                    "bin_edges": [float, ...],
                    "frequencies": [int, ...],
                },
                "skewness": float,
                "interpretation": str,
            }
        """
        if not values or len(values) < 2:
            return {"error": "Insufficient data"}
        
        try:
            values_float = [float(v) for v in values]
            min_val, max_val = min(values_float), max(values_float)
            
            # 히스토그램 생성
            if min_val == max_val:
                return {
                    "distribution": {
                        "bin_edges": [min_val, min_val],
                        "frequencies": [len(values_float)],
                    },
                    "skewness": 0,
                    "interpretation": "All values are identical",
                }
            
            bin_size = (max_val - min_val) / bins
            bin_edges = [min_val + i * bin_size for i in range(bins + 1)]
            frequencies = [0] * bins
            
            for v in values_float:
                bin_idx = int((v - min_val) / bin_size)
                if bin_idx >= bins:
                    bin_idx = bins - 1
                frequencies[bin_idx] += 1
            
            # 단순화된 skewness 계산
            mean = statistics.mean(values_float)
            median = statistics.median(values_float)
            skewness = (mean - median) / (statistics.stdev(values_float) or 1)
            
            return {
                "distribution": {
                    "bin_edges": [round(e, 2) for e in bin_edges],
                    "frequencies": frequencies,
                },
                "skewness": round(skewness, 3),
                "interpretation": "left-skewed" if skewness < -0.5 else "right-skewed" if skewness > 0.5 else "symmetric",
            }
        except Exception as e:
            return {"error": str(e)}


def register_analyzer_tools(registry) -> None:
    """Analyzer Tool 등록"""
    from .registry import Tool, ToolParameter, ToolCategory
    
    tool1 = Tool(
        name="calculate_statistics",
        description="데이터의 통계를 계산합니다 (합계, 평균, 중앙값, 표준편차 등)",
        category=ToolCategory.ANALYZER,
        parameters=[
            ToolParameter("values", "list", "분석할 숫자 리스트", required=True),
        ],
        execute=AnalyzerTool.calculate_statistics,
        cost={"time": 0.5, "tokens": 200},
    )
    registry.register(tool1)
    
    tool2 = Tool(
        name="detect_outliers",
        description="데이터에서 이상치를 탐지합니다",
        category=ToolCategory.ANALYZER,
        parameters=[
            ToolParameter("values", "list", "분석할 숫자 리스트", required=True),
            ToolParameter("method", "str", "탐지 방법 (iqr, zscore)", required=False, default="iqr"),
            ToolParameter("threshold", "float", "임계값", required=False, default=1.5),
        ],
        execute=AnalyzerTool.detect_outliers,
        cost={"time": 1.0, "tokens": 300},
    )
    registry.register(tool2)
    
    tool3 = Tool(
        name="analyze_distribution",
        description="데이터 분포를 분석합니다",
        category=ToolCategory.ANALYZER,
        parameters=[
            ToolParameter("values", "list", "분석할 숫자 리스트", required=True),
            ToolParameter("bins", "int", "히스토그램 구간 수", required=False, default=10),
        ],
        execute=AnalyzerTool.analyze_distribution,
        cost={"time": 1.0, "tokens": 300},
    )
    registry.register(tool3)

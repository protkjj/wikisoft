"""
Parser Tool: Excel 파일 파싱

책임:
- Excel 파일 읽기
- 헤더 매칭 (AI 기반)
- 데이터 정규화
"""

from typing import Any, Dict, List
import pandas as pd
from .registry import Tool, ToolParameter, ToolCategory, get_registry


class ParserTool:
    """Excel 파일 파싱 도구"""
    
    @staticmethod
    async def parse_excel(file_path: str) -> Dict[str, Any]:
        """
        Excel 파일 파싱
        
        Args:
            file_path: Excel 파일 경로
        
        Returns:
            {
                "sheets": {
                    "sheet_name": DataFrame,
                    ...
                },
                "headers": {
                    "sheet_name": [column_names],
                    ...
                },
                "row_count": int,
                "column_count": int,
            }
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = {}
            headers = {}
            total_rows = 0
            max_cols = 0
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets[sheet_name] = df
                headers[sheet_name] = df.columns.tolist()
                total_rows += len(df)
                max_cols = max(max_cols, len(df.columns))
            
            return {
                "success": True,
                "sheets": sheets,
                "headers": headers,
                "row_count": total_rows,
                "column_count": max_cols,
                "sheet_names": excel_file.sheet_names,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    async def match_headers(
        source_headers: List[str],
        target_schema: List[str],
        ai_model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """
        AI를 사용해 헤더 매칭
        
        Args:
            source_headers: 원본 Excel 헤더들
            target_schema: 목표 표준 스키마
            ai_model: 사용할 LLM
        
        Returns:
            {
                "mapping": {"source_col": "target_col", ...},
                "confidence": {
                    "source_col": 0.95,
                    ...
                },
                "unmatched": ["col1", "col2"],
            }
        """
        # 아직 mock 구현 (나중에 LLM 통합)
        return {
            "mapping": {src: tgt for src, tgt in zip(source_headers, target_schema)},
            "confidence": {src: 0.9 for src in source_headers},
            "unmatched": [],
        }
    
    @staticmethod
    async def normalize_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        데이터 정규화
        
        Args:
            df: Pandas DataFrame
        
        Returns:
            {
                "original_shape": (rows, cols),
                "normalized_shape": (rows, cols),
                "changes": {
                    "empty_rows_removed": int,
                    "columns_renamed": int,
                    "types_converted": int,
                },
            }
        """
        original_shape = df.shape
        
        # 빈 행 제거
        df_clean = df.dropna(how='all')
        empty_rows_removed = original_shape[0] - len(df_clean)
        
        # 공백 제거
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].str.strip()
        
        return {
            "success": True,
            "original_shape": original_shape,
            "normalized_shape": df_clean.shape,
            "changes": {
                "empty_rows_removed": empty_rows_removed,
                "columns_renamed": 0,
                "types_converted": 0,
            },
            "data": df_clean,
        }


def register_parser_tool(registry) -> None:
    """Parser Tool 등록"""
    tool = Tool(
        name="parse_excel",
        description="Excel 파일을 읽고 시트, 헤더, 데이터를 추출합니다",
        category=ToolCategory.PARSER,
        parameters=[
            ToolParameter(
                name="file_path",
                type="str",
                description="Excel 파일 경로",
                required=True,
            ),
        ],
        execute=ParserTool.parse_excel,
        cost={"time": 2.0, "tokens": 500},
    )
    registry.register(tool)
    
    tool_normalize = Tool(
        name="normalize_data",
        description="Excel 데이터를 정규화합니다 (공백 제거, 빈 행 삭제 등)",
        category=ToolCategory.PARSER,
        parameters=[
            ToolParameter(
                name="df",
                type="DataFrame",
                description="Pandas DataFrame",
                required=True,
            ),
        ],
        execute=ParserTool.normalize_data,
        cost={"time": 1.0, "tokens": 200},
    )
    registry.register(tool_normalize)

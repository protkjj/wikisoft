from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    """수정된 데이터 내보내기 요청"""
    filename: str
    headers: List[str]
    data: List[Dict[str, Any]]


@router.post("/xlsx")
async def export_xlsx(request: ExportRequest):
    """수정된 데이터를 Excel 파일로 내보내기
    
    Args:
        request: 파일명, 헤더, 데이터
        
    Returns:
        StreamingResponse: Excel 파일 다운로드
    """
    try:
        # 워크북 생성
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "재직자명부"
        
        # 헤더 스타일
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # 헤더 작성
        for col_idx, header in enumerate(request.headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # 데이터 작성
        for row_idx, row_data in enumerate(request.data, start=2):
            for col_idx, header in enumerate(request.headers, start=1):
                value = row_data.get(header, "")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.alignment = Alignment(horizontal="left", vertical="center")
        
        # 컬럼 너비 자동 조정
        for col_idx, header in enumerate(request.headers, start=1):
            max_length = len(str(header))
            for row_idx in range(2, len(request.data) + 2):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            
            # 최대 50자로 제한
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = adjusted_width
        
        # 파일명 생성 (원본명_수정본_날짜.xlsx)
        base_name = request.filename.rsplit(".", 1)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{base_name}_수정본_{timestamp}.xlsx"
        
        # BytesIO에 저장
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{output_filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 생성 실패: {str(e)}")

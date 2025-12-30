"""
엑셀 파일 탐색 및 시트별 데이터 로드
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List


class ExcelLoader:
    """엑셀 파일을 탐색하고 시트별로 데이터를 로드하는 클래스"""
    
    def __init__(self, data_dir: Path):
        """
        Args:
            data_dir: 엑셀 파일이 있는 디렉토리 경로
        """
        self.data_dir = Path(data_dir)
    
    def find_excel_files(self) -> List[Path]:
        """
        data_dir에서 모든 엑셀 파일(.xlsx, .xls)을 찾아 반환
        
        Returns:
            엑셀 파일 경로 리스트
        """
        excel_files = []
        
        # .xlsx 파일 찾기
        excel_files.extend(self.data_dir.glob("*.xlsx"))
        # .xls 파일 찾기
        excel_files.extend(self.data_dir.glob("*.xls"))
        
        return sorted(excel_files)
    
    def load_excel(self, file_path: Path) -> Dict[str, pd.DataFrame]:
        """
        엑셀 파일의 모든 시트를 읽어서 딕셔너리로 반환
        
        Args:
            file_path: 엑셀 파일 경로
            
        Returns:
            {시트명: DataFrame} 형태의 딕셔너리
        """
        excel_file = pd.ExcelFile(file_path)
        dataframes = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                # 시트 데이터 읽기
                df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    engine='openpyxl'
                )
                
                # 빈 시트가 아닌 경우만 저장
                if not df.empty:
                    dataframes[sheet_name] = df
                    print(f"      - {sheet_name}: {len(df)}행 로드 완료")
            except Exception as e:
                print(f"      ⚠️  시트 '{sheet_name}' 로드 실패: {str(e)}")
                continue
        
        if not dataframes:
            raise ValueError(f"엑셀 파일에서 유효한 데이터를 찾을 수 없습니다: {file_path}")
        
        return dataframes
    
    def get_sheet_info(self, file_path: Path) -> Dict[str, int]:
        """
        엑셀 파일의 시트별 행 수 정보 반환
        
        Args:
            file_path: 엑셀 파일 경로
            
        Returns:
            {시트명: 행 수} 형태의 딕셔너리
        """
        excel_file = pd.ExcelFile(file_path)
        sheet_info = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
                sheet_info[sheet_name] = len(df)
            except:
                sheet_info[sheet_name] = 0
        
        return sheet_info

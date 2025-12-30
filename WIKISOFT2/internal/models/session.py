from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
import uuid


@dataclass
class Session:
    """
    사용자 세션 관리
    - 원본/현재 데이터프레임
    - 검증 결과 & 이상치
    - 챗봇 질문/답변
    - 수정 이력
    """
    session_id: str
    original_dataframe: pd.DataFrame
    current_dataframe: pd.DataFrame
    diagnostic_answers: Dict[str, str]  # Q1-Q5 답변
    created_at: datetime
    last_accessed: datetime
    token: str
    
    # 검증 결과
    validation_result: Dict = field(default_factory=dict)  # errors, warnings
    anomalies: List[Dict] = field(default_factory=list)  # ML 이상치 목록
    
    # 챗봇 질문/답변
    chatbot_questions: List[Dict] = field(default_factory=list)  # Q 목록
    chatbot_answers: Dict[str, str] = field(default_factory=dict)  # {question_id: answer}
    
    # 수정 이력
    modified_cells: Dict[str, dict] = field(default_factory=dict)  # {row_col: {original, new}}
    snapshots: Dict[str, pd.DataFrame] = field(default_factory=dict)  # 스냅샷
    
    # 분석 캐시
    analytics_cache: Optional[Dict] = None
    parsed_data: Optional[Dict] = None
    
    @classmethod
    def create(cls, df: pd.DataFrame, diagnostic_answers: Dict[str, str]) -> "Session":
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        now = datetime.now()
        
        return cls(
            session_id=session_id,
            original_dataframe=df.copy(),
            current_dataframe=df.copy(),
            diagnostic_answers=diagnostic_answers,
            created_at=now,
            last_accessed=now,
            token=token,
            parsed_data=None
        )
    
    def update_access_time(self):
        """마지막 접근 시간 업데이트"""
        self.last_accessed = datetime.now()
    
    def save_snapshot(self, name: str):
        """현재 데이터프레임 스냅샷 저장"""
        self.snapshots[name] = self.current_dataframe.copy()
    
    def restore_snapshot(self, name: str) -> bool:
        """스냅샷에서 복구"""
        if name in self.snapshots:
            self.current_dataframe = self.snapshots[name].copy()
            return True
        return False
    
    def get_modified_count(self) -> int:
        """수정된 셀 개수"""
        return len(self.modified_cells)

"""
Schema Configuration Manager

스키마 설정 중앙 관리
현재: 하드코딩된 20개 필드
미래: JSON/DB에서 로드 가능
"""

from typing import Dict, List, Optional
import os
import json

try:
    import yaml  # 선택적 의존성: 없으면 JSON만 지원
except Exception:
    yaml = None


class SchemaConfig:
    """스키마 설정 관리"""
    
    # 현재: 하드코딩된 표준 스키마 (내부적으로 사용)
    _STANDARD_SCHEMA = {
        # 직원 정보
        "employee_type": "str",
        "name": "str",
        "employee_id": "str",
        "department": "str",
        "position": "str",
        "join_date": "date",
        
        # 급여 정보
        "salary": "float",
        "annual_salary": "float",
        "bonus": "float",
        "allowance": "float",
        
        # 근무 정보
        "working_hours": "float",
        "start_date": "date",
        "end_date": "date",
        "status": "str",
        
        # 퇴직 정보
        "retirement_date": "date",
        "retirement_reason": "str",
        "severance": "float",
        
        # 추가 정보
        "notes": "str",
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        초기화
        
        Args:
            config_file: 설정 파일 경로 (현재는 무시, 미래용)
        """
        self.config_file = config_file
        self._schema = self._STANDARD_SCHEMA.copy()
    
    def get_schema(self) -> Dict[str, str]:
        """
        스키마 조회
        
        Returns:
            {"field_name": "type", ...}
        """
        return self._schema.copy()
    
    def get_field_type(self, field_name: str) -> Optional[str]:
        """
        특정 필드의 타입 조회
        
        Args:
            field_name: 필드명
        
        Returns:
            필드 타입 또는 None
        """
        return self._schema.get(field_name)
    
    def get_required_fields(self) -> List[str]:
        """
        필수 필드 조회
        
        Returns:
            필수 필드 목록
        """
        required = [
            "employee_type",
            "name",
            "salary",
            "status"
        ]
        return required
    
    def validate_field(self, field_name: str, value) -> bool:
        """
        필드 값이 유효한지 확인
        
        Args:
            field_name: 필드명
            value: 필드 값
        
        Returns:
            True if valid
        """
        field_type = self.get_field_type(field_name)
        
        if field_type is None:
            return False  # 정의되지 않은 필드
        
        if field_type == "str":
            return isinstance(value, str)
        elif field_type == "float":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif field_type == "date":
            # 간단한 날짜 검증
            try:
                from datetime import datetime
                datetime.fromisoformat(str(value))
                return True
            except (ValueError, TypeError):
                return False
        else:
            return True
    
    def load_from_file(self, file_path: str) -> bool:
        """
        JSON/YAML에서 스키마 로드 (외부 설정 병합)
        
        Args:
            file_path: 설정 파일 경로
        
        Returns:
            True if successful
        """
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.lower().endswith(('.yml', '.yaml')) and yaml is not None:
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)

            # 외부 파일은 {"schema": {field: type}} 형식을 권장
            external_schema = data.get("schema") if isinstance(data, dict) else None
            if isinstance(external_schema, dict):
                # 하드코딩 스키마에 병합 (외부 설정 우선 적용)
                self._schema.update(external_schema)
                return True
            return False
        except Exception:
            return False
    
    def add_field(self, field_name: str, field_type: str) -> bool:
        """
        새로운 필드 추가 (Runtime)
        
        Args:
            field_name: 필드명
            field_type: 필드 타입
        
        Returns:
            True if successful
        """
        if field_name in self._schema:
            return False  # 이미 존재
        
        self._schema[field_name] = field_type
        return True
    
    def remove_field(self, field_name: str) -> bool:
        """
        필드 제거 (Runtime)
        
        Args:
            field_name: 필드명
        
        Returns:
            True if successful
        """
        if field_name not in self._schema:
            return False
        
        del self._schema[field_name]
        return True


# 전역 인스턴스
_global_schema_config = SchemaConfig()


def get_schema_config() -> SchemaConfig:
    """전역 SchemaConfig 조회"""
    return _global_schema_config

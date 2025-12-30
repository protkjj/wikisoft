"""
Configuration Module

현재는 하드코딩 그대로 사용
미래: JSON/YAML/DB에서 로드 가능하도록 설계
"""

from .schema_config import SchemaConfig
from .prompt_config import PromptConfig

__all__ = ["SchemaConfig", "PromptConfig"]

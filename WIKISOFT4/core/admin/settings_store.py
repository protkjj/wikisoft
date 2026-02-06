"""
System Settings Store

SQLite 기반 시스템 설정 저장소
"""

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from core.database import get_db, get_cursor


class SystemSettings(BaseModel):
    """시스템 설정 모델."""

    minimum_wage: int = Field(default=2060740, description="최저임금 (월)")
    retirement_age: int = Field(default=60, description="정년 나이")
    validation_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="검증 신뢰도 임계값"
    )
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="최대 파일 크기 (MB)")
    allowed_extensions: list[str] = Field(
        default=[".xls", ".xlsx"],
        description="허용된 파일 확장자"
    )


# 기본 설정 키 목록
_DEFAULT_SETTINGS = SystemSettings()


class SettingsStore:
    """시스템 설정 저장소 (SQLite 기반)."""

    def _load_from_db(self) -> dict[str, Any]:
        """DB에서 전체 설정 로드."""
        db = get_db()
        rows = db.execute("SELECT key, value FROM system_settings").fetchall()
        data = {}
        for row in rows:
            try:
                data[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                data[row["key"]] = row["value"]
        return data

    def _save_to_db(self, settings: SystemSettings) -> None:
        """설정을 DB에 저장."""
        now = datetime.now(timezone.utc).isoformat()
        data = settings.model_dump()
        with get_cursor() as cur:
            for key, value in data.items():
                cur.execute("""
                    INSERT OR REPLACE INTO system_settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, json.dumps(value, ensure_ascii=False), now))

    def get(self) -> SystemSettings:
        """현재 설정 반환."""
        data = self._load_from_db()
        if not data:
            # DB에 설정이 없으면 기본값 저장 후 반환
            defaults = SystemSettings()
            self._save_to_db(defaults)
            return defaults
        return SystemSettings(**data)

    def update(self, updates: dict[str, Any]) -> SystemSettings:
        """설정 업데이트."""
        current = self.get().model_dump()
        current.update(updates)
        settings = SystemSettings(**current)
        self._save_to_db(settings)
        return settings

    def reset(self) -> SystemSettings:
        """설정 초기화."""
        settings = SystemSettings()
        self._save_to_db(settings)
        return settings


# Global singleton
_settings_store: SettingsStore | None = None


def get_settings_store() -> SettingsStore:
    """설정 저장소 싱글톤 반환."""
    global _settings_store
    if _settings_store is None:
        _settings_store = SettingsStore()
    return _settings_store


def get_settings() -> SystemSettings:
    """현재 시스템 설정 반환."""
    return get_settings_store().get()


def update_settings(updates: dict[str, Any]) -> SystemSettings:
    """시스템 설정 업데이트."""
    return get_settings_store().update(updates)

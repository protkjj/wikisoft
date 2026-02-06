"""
Training Data Manager

학습 데이터 파일 관리 (조회, 삭제)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TrainingFile(BaseModel):
    """학습 데이터 파일 정보."""

    filename: str
    file_type: str  # 'validation', 'layer1_error', 'case', etc.
    size_bytes: int
    created_at: datetime
    modified_at: datetime


class TrainingFileDetail(TrainingFile):
    """학습 데이터 파일 상세 (내용 포함)."""

    content: dict[str, Any] = Field(default_factory=dict)


class TrainingManager:
    """학습 데이터 관리자."""

    def __init__(self, training_data_path: Path | None = None):
        if training_data_path is None:
            # Default: WIKISOFT4/training_data/
            self.training_data_path = Path(__file__).parent.parent.parent / "training_data"
        else:
            self.training_data_path = training_data_path

    def list_files(self) -> list[TrainingFile]:
        """학습 데이터 파일 목록 조회."""
        if not self.training_data_path.exists():
            return []

        files = []
        for file_path in self.training_data_path.glob("*.json"):
            if file_path.is_file():
                stat = file_path.stat()
                file_type = self._detect_file_type(file_path.name)
                files.append(TrainingFile(
                    filename=file_path.name,
                    file_type=file_type,
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                ))

        # Sort by modified_at descending
        files.sort(key=lambda f: f.modified_at, reverse=True)
        return files

    def _detect_file_type(self, filename: str) -> str:
        """파일 타입 감지."""
        if filename.startswith("layer1_error"):
            return "layer1_error"
        elif filename.startswith("layer2_error"):
            return "layer2_error"
        elif filename.startswith("validation"):
            return "validation"
        elif filename.startswith("case"):
            return "case"
        elif filename.startswith("correction"):
            return "correction"
        else:
            return "other"

    def get_file(self, filename: str) -> TrainingFileDetail | None:
        """학습 데이터 파일 상세 조회."""
        # Prevent path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return None

        file_path = self.training_data_path / filename
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except (json.JSONDecodeError, IOError):
            content = {"error": "Failed to parse JSON"}

        stat = file_path.stat()
        return TrainingFileDetail(
            filename=filename,
            file_type=self._detect_file_type(filename),
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            content=content,
        )

    def delete_file(self, filename: str) -> bool:
        """학습 데이터 파일 삭제."""
        # Prevent path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return False

        file_path = self.training_data_path / filename
        if not file_path.exists() or not file_path.is_file():
            return False

        try:
            file_path.unlink()
            return True
        except IOError:
            return False

    def get_stats(self) -> dict[str, Any]:
        """학습 데이터 통계."""
        files = self.list_files()

        type_counts: dict[str, int] = {}
        total_size = 0

        for f in files:
            type_counts[f.file_type] = type_counts.get(f.file_type, 0) + 1
            total_size += f.size_bytes

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "type_counts": type_counts,
        }


# Global singleton
_training_manager: TrainingManager | None = None


def get_training_manager() -> TrainingManager:
    """학습 데이터 관리자 싱글톤 반환."""
    global _training_manager
    if _training_manager is None:
        _training_manager = TrainingManager()
    return _training_manager

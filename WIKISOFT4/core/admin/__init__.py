"""Admin module for WIKISOFT4."""

from .settings_store import SettingsStore, get_settings, update_settings
from .training_manager import TrainingManager, get_training_manager

__all__ = [
    "SettingsStore",
    "get_settings",
    "update_settings",
    "TrainingManager",
    "get_training_manager",
]

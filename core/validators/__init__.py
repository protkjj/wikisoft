"""
WIKISOFT 4.1 Validators

3-layer validation system migrated from WIKISOFT3:
- Layer 1: Format validation (dates, types, ranges)
- Layer 2: Cross-validation (duplicates, logic)
- Layer 3: AI-assisted validation with domain context
"""

from .validator import validate_with_diagnostics, validate_mapped_data
from .validation_layer1 import validate_layer1
from .validation_layer2 import validate_layer2
from .validation_layer_ai import validate_with_ai
from .duplicate_detector import find_duplicates

__all__ = [
    "validate_with_diagnostics",
    "validate_mapped_data",
    "validate_layer1",
    "validate_layer2",
    "validate_with_ai",
    "find_duplicates",
]

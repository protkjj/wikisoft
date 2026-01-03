"""
WIKISOFT 4.1 Validators

3-layer validation system migrated from WIKISOFT3:
- Layer 1: Format validation (dates, types, ranges)
- Layer 2: Cross-validation (duplicates, logic)
- Layer 3: AI-assisted validation with domain context
"""

# Lazy imports to avoid circular dependencies
__all__ = [
    "validator",
    "validation_layer1",
    "validation_layer2",
    "duplicate_detector",
]

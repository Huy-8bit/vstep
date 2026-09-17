"""Compatibility import; reference layer is the single specification owner."""

from app.vstep_reference.reading_blueprints import READING_BLUEPRINT, ReadingFullTestBlueprint, ReadingSlot

ReadingTestBlueprint = ReadingFullTestBlueprint
__all__ = ["READING_BLUEPRINT", "ReadingFullTestBlueprint", "ReadingTestBlueprint", "ReadingSlot"]

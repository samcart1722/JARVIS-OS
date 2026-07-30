"""Specialist contract."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.goal import Goal
from app.cognition.planning.plan import Plan


class Specialist(Protocol):
    """Define a specialist that can plan for supported user goals."""

    def can_handle(self, goal: Goal) -> bool:
        """Return whether this specialist supports the goal."""

    def create_plan(self, context: CognitiveContext) -> Plan:
        """Create a high-level plan for the supported goal."""

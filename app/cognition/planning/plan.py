"""High-level planning domain object."""

from dataclasses import dataclass

from app.cognition.planning.plan_step import PlanStep


@dataclass(frozen=True)
class Plan:
    """Represent an ordered sequence of high-level steps."""

    steps: tuple[PlanStep, ...]

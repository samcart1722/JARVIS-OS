"""User goal domain object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Goal:
    """Represent the objective expressed by a user."""

    description: str

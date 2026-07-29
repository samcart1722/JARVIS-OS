"""Specialist routing registry."""

from app.cognition.domain.domain import Domain
from app.cognition.specialists.default_specialist import DefaultSpecialist
from app.cognition.specialists.specialist import Specialist


class SpecialistRouter:
    """Resolve specialists registered for cognitive domains."""

    def __init__(self) -> None:
        default_specialist = DefaultSpecialist()
        self._registry: dict[Domain, Specialist] = {
            domain: default_specialist for domain in Domain
        }

    def route(self, domain: Domain) -> Specialist:
        """Return the specialist registered for the supplied domain."""
        return self._registry[domain]

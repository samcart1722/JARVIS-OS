"""Infrastructure-independent contract for bounded local command interpretation."""

from typing import Protocol

from app.cognition.interpretation.models import LocalCommandInterpretation


class LocalCommandInterpreter(Protocol):
    def interpret(self, text: str) -> LocalCommandInterpretation: ...

"""Infrastructure-independent contract for bounded local command interpretation."""

from typing import Protocol

from app.cognition.interpretation.models import LocalCommandInterpretation
from app.cognition.local_resolution.models import WorkspaceIdentity


class LocalCommandInterpreter(Protocol):
    def interpret(
        self, text: str, workspace: WorkspaceIdentity
    ) -> LocalCommandInterpretation: ...

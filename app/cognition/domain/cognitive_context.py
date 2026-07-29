"""Domain context shared by the cognitive pipeline stages."""

from dataclasses import dataclass

from app.cognition.planning.goal import Goal


@dataclass(frozen=True)
class CognitiveContext:
    """Represent all currently available context for a cognitive request."""

    raw_input: str
    normalized_input: str
    goal: Goal | None = None
    task: str | None = None
    workspace: str | None = None
    conversation_context: tuple[str, ...] = ()
    memory_snapshot: tuple[str, ...] = ()
    initial_evidence: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

"""Result model for plan execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionResult:
    """Represent the outcome of executing a high-level plan."""

    success: bool
    completed_steps: tuple[str, ...]
    outputs: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

"""Result model for capability execution."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CapabilityResult:
    """Represent the outcome of executing a cognitive capability."""

    success: bool
    outputs: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    error_code: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

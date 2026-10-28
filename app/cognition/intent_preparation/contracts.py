"""Minimal core port for bounded extraction, separate from cognitive reasoning."""

from typing import Protocol


class IntentPreparationProvider(Protocol):
    def prepare(self, text: str) -> str:
        """Return untrusted closed-candidate JSON for an already bounded request.

        Implementations must not infer execution context or use authority ports.
        A returned string is never accepted data until strict parsing, grounding
        and deterministic validation complete. This port invokes no provider here.
        """
        ...

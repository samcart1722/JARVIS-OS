"""
Reasoning Domain

UserRequest Entity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class UserRequest:
    """
    Represents a single request entering the reasoning domain.

    A UserRequest is immutable and uniquely identifies one reasoning cycle.
    """

    content: str
    request_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        normalized = self.content.strip()

        if not normalized:
            raise ValueError("UserRequest content cannot be empty.")

        object.__setattr__(self, "content", normalized)
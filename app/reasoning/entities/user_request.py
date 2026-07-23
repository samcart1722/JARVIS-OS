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
    Represents a single user request entering the Reasoning Engine.

    A UserRequest is immutable and uniquely identifies one reasoning cycle.
    """

    content: str
    request_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        content = self.content.strip()

        if not content:
            raise ValueError("UserRequest content cannot be empty.")

        object.__setattr__(self, "content", content)

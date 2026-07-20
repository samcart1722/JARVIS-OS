from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReflectionStatus(str, Enum):
    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"


@dataclass(slots=True)
class ReflectionResult:
    """
    Resultado del proceso de reflexión.
    """

    status: ReflectionStatus
    score: float = 1.0
    feedback: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

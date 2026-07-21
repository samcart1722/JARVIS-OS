from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class MemoryFact:
    key: str
    value: str
    confidence: float = 1.0
    source: str = "conversation"
    created_at: datetime = datetime.now(
        UTC,
    )

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class KnowledgeUnit:

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    title: str = ""

    summary: str = ""

    content: str = ""

    source: str = ""

    author: str = ""

    category: str = ""

    tags: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)

    updated_at: datetime = field(default_factory=datetime.now)

    confidence: float = 1.0

    priority: int = 1

    related_units: List[str] = field(default_factory=list)
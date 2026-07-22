"""
Default implementation of the MemoryValidator contract.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryValidator
from app.cognition.memory.domain.entities import MemoryFact


class DefaultValidator(MemoryValidator):
    """
    Basic validator for MemoryFact instances.

    The initial implementation only verifies that the
    memory contains non-empty content. More advanced
    validation rules will be added in future iterations.
    """

    async def validate(
        self,
        memory: MemoryFact,
    ) -> bool:
        return bool(memory.content.strip())

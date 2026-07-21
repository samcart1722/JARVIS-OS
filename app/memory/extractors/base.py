from abc import ABC, abstractmethod

from app.memory.facts import MemoryFact


class BaseMemoryExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        text: str,
        original: str,
    ) -> list[MemoryFact]: ...

from dataclasses import dataclass

from app.memory.facts import MemoryFact


@dataclass(slots=True)
class RetrievedMemory:
    """
    Representa una memoria recuperada durante
    el proceso de búsqueda.

    Contiene la memoria original y la información
    asociada a su recuperación.
    """

    memory: MemoryFact

    score: float = 1.0

    retrieval_method: str = "keyword"

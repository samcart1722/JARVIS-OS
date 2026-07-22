from dataclasses import dataclass


@dataclass(slots=True)
class RetrievedMemory:
    """
    Representa una memoria recuperada
    durante el proceso de búsqueda.
    """

    key: str

    value: str

    score: float = 1.0

    source: str = "keyword"

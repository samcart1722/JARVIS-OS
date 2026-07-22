from abc import ABC, abstractmethod

from app.memory.models.retrieved_memory import RetrievedMemory


class RankingStrategy(ABC):
    """
    Contrato base para cualquier estrategia
    de puntuación de memorias.
    """

    @abstractmethod
    def apply(
        self,
        memories: list[RetrievedMemory],
    ) -> None:
        """
        Modifica el score de las memorias
        recibidas.

        La estrategia debe trabajar sobre la
        misma lista, sin crear una nueva.
        """
        raise NotImplementedError

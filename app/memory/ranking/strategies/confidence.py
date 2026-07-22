from app.memory.models.retrieved_memory import RetrievedMemory
from app.memory.ranking.strategy import RankingStrategy


class ConfidenceStrategy(RankingStrategy):
    """
    Ajusta el score de cada memoria utilizando
    su nivel de confianza.
    """

    def apply(
        self,
        memories: list[RetrievedMemory],
    ) -> None:

        for memory in memories:
            memory.score *= memory.memory.confidence

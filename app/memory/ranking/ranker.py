from app.memory.models.retrieved_memory import RetrievedMemory
from app.memory.ranking.strategy import RankingStrategy


class MemoryRanker:
    """
    Aplica estrategias de ranking sobre
    una colección de memorias.

    No ordena ni filtra resultados.
    """

    def __init__(
        self,
        strategies: list[RankingStrategy],
    ) -> None:
        self.strategies = strategies

    def rank(
        self,
        memories: list[RetrievedMemory],
    ) -> list[RetrievedMemory]:

        for strategy in self.strategies:
            strategy.apply(
                memories,
            )

        return memories

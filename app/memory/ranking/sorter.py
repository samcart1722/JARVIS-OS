from app.memory.models.retrieved_memory import RetrievedMemory


class MemorySorter:
    """
    Ordena memorias utilizando el score
    calculado por el MemoryRanker.
    """

    def sort(
        self,
        memories: list[RetrievedMemory],
    ) -> list[RetrievedMemory]:

        return sorted(
            memories,
            key=lambda memory: memory.score,
            reverse=True,
        )

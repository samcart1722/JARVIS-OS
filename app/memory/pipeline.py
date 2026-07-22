from app.context.assembler import ContextAssembler
from app.core.logger import logger
from app.memory.facts import MemoryFact
from app.memory.manager import MemoryManager
from app.memory.ranking.ranker import MemoryRanker
from app.memory.ranking.sorter import MemorySorter
from app.memory.ranking.strategies.confidence import ConfidenceStrategy
from app.memory.retriever import MemoryRetriever


class MemoryPipeline:
    """
    Orquesta el pipeline cognitivo de memoria.

    Flujo:

        Retriever
            ↓
        Ranker
            ↓
        Sorter
            ↓
        ContextAssembler
            ↓
        list[MemoryFact]
    """

    def __init__(
        self,
        memory: MemoryManager,
    ) -> None:

        self.retriever = MemoryRetriever(
            memory,
        )

        self.ranker = MemoryRanker(
            strategies=[
                ConfidenceStrategy(),
            ],
        )

        self.sorter = MemorySorter()

        self.assembler = ContextAssembler()

    def retrieve(
        self,
        user_input: str,
    ) -> list[MemoryFact]:

        retrieved_memories = self.retriever.retrieve(
            user_input,
        )

        ranked_memories = self.ranker.rank(
            retrieved_memories,
        )

        sorted_memories = self.sorter.sort(
            ranked_memories,
        )

        memories = self.assembler.assemble(
            sorted_memories,
        )
        logger.info(
            "----------------------------------------\n"
            "MemoryPipeline\n"
            "Retriever: {}\n"
            "Ranker: {}\n"
            "Sorter: {}\n"
            "Assembler: {}\n"
            "----------------------------------------",
            retrieved_memories,
            ranked_memories,
            sorted_memories,
            memories,
        )

        return memories

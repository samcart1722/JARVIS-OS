from app.memory.facts import MemoryFact
from app.memory.models.retrieved_memory import RetrievedMemory


class ContextAssembler:
    """
    Selecciona las memorias que serán enviadas
    al PromptBuilder.

    Este componente decide qué recuerdos
    sobreviven después del proceso de ranking.
    """

    def __init__(
        self,
        max_memories: int = 10,
    ) -> None:

        self.max_memories = max_memories

    def assemble(
        self,
        memories: list[RetrievedMemory],
    ) -> list[MemoryFact]:
        """
        Convierte memorias recuperadas en
        memorias listas para el PromptBuilder.
        """

        selected = memories[: self.max_memories]

        return [memory.memory for memory in selected]

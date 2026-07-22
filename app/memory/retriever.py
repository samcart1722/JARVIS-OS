from app.memory.intent_analyzer import IntentAnalyzer
from app.memory.keyword_intent_analyzer import KeywordIntentAnalyzer
from app.memory.manager import MemoryManager
from app.memory.models.retrieved_memory import RetrievedMemory


class MemoryRetriever:
    """
    Recupera únicamente los recuerdos relevantes
    para la conversación actual.
    """

    def __init__(
        self,
        memory: MemoryManager,
        analyzer: IntentAnalyzer | None = None,
    ) -> None:
        self.memory = memory
        self.analyzer = analyzer or KeywordIntentAnalyzer()

    def retrieve(
        self,
        user_input: str,
    ) -> list[RetrievedMemory]:
        """
        Devuelve únicamente los recuerdos
        relevantes para el mensaje del usuario.
        """

        intent = self.analyzer.analyze(
            user_input,
        )

        memories: list[RetrievedMemory] = []

        if "project" in intent.topics:
            fact = self.memory.recall(
                "project",
            )

            if fact:
                memories.append(
                    RetrievedMemory(
                        memory=fact,
                    )
                )

        if "medical" in intent.topics:
            fact = self.memory.recall(
                "profession",
            )

            if fact:
                memories.append(
                    RetrievedMemory(
                        memory=fact,
                    )
                )

        if "profile" in intent.topics:
            for fact in self.memory.knowledge():
                if any(memory.memory.key == fact.key for memory in memories):
                    continue

                memories.append(
                    RetrievedMemory(
                        memory=fact,
                    )
                )

        return memories

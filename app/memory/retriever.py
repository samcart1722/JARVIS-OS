from app.memory.intent_analyzer import IntentAnalyzer
from app.memory.keyword_intent_analyzer import KeywordIntentAnalyzer
from app.memory.manager import MemoryManager


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
    ) -> dict[str, str]:
        """
        Devuelve únicamente los recuerdos
        relevantes para el mensaje del usuario.
        """

        intent = self.analyzer.analyze(
            user_input,
        )

        memories: dict[str, str] = {}

        if "project" in intent.topics:
            project = self.memory.recall(
                "project",
            )

            if project:
                memories["project"] = project

        if "medical" in intent.topics:
            profession = self.memory.recall(
                "profession",
            )

            if profession:
                memories["profession"] = profession

        return memories

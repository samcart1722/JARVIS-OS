from app.prompt.types import PromptType


class PromptStrategy:
    """
    Determina qué tipo de prompt debe utilizarse
    según la intención detectada y el contexto.
    """

    def select(
        self,
        intent: str,
    ) -> PromptType:

        intent = intent.lower()

        if intent == "coding":
            return PromptType.CODING

        if intent == "medical":
            return PromptType.MEDICAL

        if intent == "research":
            return PromptType.RESEARCH

        if intent == "browser":
            return PromptType.BROWSER

        if intent == "planning":
            return PromptType.PLANNING

        if intent == "system":
            return PromptType.SYSTEM

        return PromptType.GENERAL

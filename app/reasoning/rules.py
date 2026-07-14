from app.reasoning.models import (
    ActionType,
    Decision,
)


class ReasoningRules:

    def decide(
        self,
        user_input: str,
    ) -> Decision:

        text = user_input.lower()

        if any(
            phrase in text
            for phrase in [
                "mi proyecto",
                "mi empresa",
                "mi nombre",
            ]
        ):

            return Decision(
                action=ActionType.MEMORY,
                reason="Stored personal knowledge.",
            )

        if any(
            phrase in text
            for phrase in [
                "que sabes sobre",
                "que conozco sobre",
                "muéstrame",
            ]
        ):

            return Decision(
                action=ActionType.KNOWLEDGE,
                reason="Knowledge lookup.",
            )

        if any(
            phrase in text
            for phrase in [
                "abre",
                "ejecuta",
                "inicia",
            ]
        ):

            return Decision(
                action=ActionType.TOOL,
                reason="Tool execution.",
            )

        if any(
            phrase in text
            for phrase in [
                "busca",
                "investiga",
                "últimas noticias",
                "novedades",
            ]
        ):

            return Decision(
                action=ActionType.BROWSER,
                reason="Internet search required.",
            )

        return Decision(
            action=ActionType.MODEL,
            reason="General reasoning.",
        )
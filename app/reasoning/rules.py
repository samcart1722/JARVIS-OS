from app.language.intents import Intent
from app.language.matcher import IntentMatcher
from app.language.normalizer import TextNormalizer
from app.reasoning.models import (
    ActionType,
    Decision,
)


class ReasoningRules:
    def __init__(self):

        self.normalizer = TextNormalizer()

        self.matcher = IntentMatcher()

    def decide(
        self,
        user_input: str,
    ) -> Decision:

        text = self.normalizer.normalize(user_input)

        intent = self.matcher.match(text)

        print()
        print("========== LANGUAGE ==========")
        print(f"NORMALIZED: {text}")
        print(f"INTENT    : {intent}")
        print("==============================")
        print()

        # ==========================
        # Memory
        # ==========================

        if intent in (
            Intent.PERSONAL_MEMORY,
            Intent.PROJECT_QUERY,
            Intent.PROJECT_LIST,
        ):
            return Decision(
                action=ActionType.MEMORY,
                reason="Memory request.",
                intent=intent.value,
            )

        # ==========================
        # Knowledge
        # ==========================

        if intent == Intent.KNOWLEDGE_QUERY:
            return Decision(
                action=ActionType.KNOWLEDGE,
                reason="Knowledge lookup.",
                intent=intent.value,
            )

        # ==========================
        # Browser
        # ==========================

        if intent == Intent.WEB_SEARCH:
            return Decision(
                action=ActionType.BROWSER,
                reason="Internet search.",
                intent=intent.value,
            )

        # ==========================
        # Tools
        # ==========================

        if intent == Intent.TOOL_EXECUTION:
            return Decision(
                action=ActionType.TOOL,
                reason="Tool execution.",
                intent=intent.value,
            )

        # ==========================
        # Default
        # ==========================

        return Decision(
            action=ActionType.MODEL,
            reason="General conversation.",
            intent=Intent.GENERAL_CHAT.value,
        )

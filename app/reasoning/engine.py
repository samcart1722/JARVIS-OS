from app.core.container import container
from app.reasoning.models import ActionType
from app.reasoning.rules import ReasoningRules


class ReasoningEngine:

    def __init__(self):

        self.rules = ReasoningRules()

        self.memory = container.memory

        self.context = container.context

        self.knowledge = getattr(
            container,
            "knowledge",
            None,
        )

        self.tools = container.tools

        self.model = container.model

    def process(
        self,
        user_input: str,
    ):

        decision = self.rules.decide(user_input)

        # ==========================================
        # MEMORY
        # ==========================================

        if decision.action == ActionType.MEMORY:

            response = self.memory.answer(
                user_input,
            )

            if response:

                return response

            return "No encontré información en la memoria."

        # ==========================================
        # KNOWLEDGE
        # ==========================================

        if decision.action == ActionType.KNOWLEDGE:

            if self.knowledge:

                return self.knowledge.answer(
                    user_input,
                )

            return "Knowledge Engine no disponible."

        # ==========================================
        # TOOLS
        # ==========================================

        if decision.action == ActionType.TOOL:

            return self.tools.execute(
                user_input,
            )

        # ==========================================
        # BROWSER
        # ==========================================

        if decision.action == ActionType.BROWSER:

            prompt = self.context.build_prompt(
                user_input,
            )

            return self.model.chat(prompt)

        # ==========================================
        # MODEL
        # ==========================================

        prompt = self.context.build_prompt(
            user_input,
        )

        return self.model.chat(prompt)
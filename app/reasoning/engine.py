from app.core.container import container
from app.reasoning.models import ActionType
from app.reasoning.rules import ReasoningRules
from app.response.models import Response, ResponseType


class ReasoningEngine:

    def __init__(self):

        self.rules = ReasoningRules()

        self.memory = container.memory

        self.context = container.context

        self.prompt = container.prompt

        self.response = container.response

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

        decision = self.rules.decide(
            user_input,
        )

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
        # CONTEXTO
        # ==========================================

        context = self.context.build_context(
            user_input,
        )

        # ==========================================
        # PROMPT FINAL
        # ==========================================

        prompt = self.prompt.build_prompt(
            intent=decision.intent,
            context=context,
            user_input=user_input,
        )

        # ==========================================
        # MODEL
        # ==========================================

        model_response = self.model.chat(
            prompt,
        )

        response = Response(
            content=model_response,
            response_type=ResponseType.TEXT,
        )

        processed = self.response.process(
            response,
        )

        return processed.content
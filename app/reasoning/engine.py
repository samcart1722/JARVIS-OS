from app.core.container import container
from app.reasoning.models import ActionType
from app.reasoning.rules import ReasoningRules
from app.response.models import Response, ResponseType


class ReasoningEngine:
    def __init__(self):

        self.rules = ReasoningRules()

        self.memory = container.memory

        self.context = container.context

        self.conversation = container.conversation

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

        self.conversation.add_user_message(
            user_input,
        )

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
                self.conversation.add_assistant_message(
                    response,
                )

                return response

            response = "No encontré información en la memoria."

            self.conversation.add_assistant_message(
                response,
            )

            return response

        # ==========================================
        # KNOWLEDGE
        # ==========================================

        if decision.action == ActionType.KNOWLEDGE:
            if self.knowledge:
                response = self.knowledge.answer(
                    user_input,
                )

                self.conversation.add_assistant_message(
                    response,
                )

                return response

            response = "Knowledge Engine no disponible."

            self.conversation.add_assistant_message(
                response,
            )

            return response

        # ==========================================
        # TOOLS
        # ==========================================

        if decision.action == ActionType.TOOL:
            response = self.tools.execute(
                user_input,
            )

            self.conversation.add_tool_message(
                str(response),
            )

            return response

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

        self.conversation.add_assistant_message(
            processed.content,
        )

        return processed.content

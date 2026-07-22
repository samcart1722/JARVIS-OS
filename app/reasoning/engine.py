from app.core.container import container
from app.core.logger import logger
from app.memory.intelligence import MemoryIntelligence
from app.reasoning.models import ActionType
from app.reasoning.rules import ReasoningRules
from app.reflection.models import ReflectionStatus
from app.response.models import Response, ResponseType


class ReasoningEngine:
    def __init__(
        self,
    ):

        self.rules = ReasoningRules()

        self.memory = container.memory

        self.memory_ai = MemoryIntelligence()

        self.context = container.context

        self.conversation = container.conversation

        self.prompt = container.prompt

        self.response = container.response

        self.reflection = container.reflection

        self.knowledge = getattr(
            container,
            "knowledge",
            None,
        )

        self.tools = container.tools

        self.models = container.models

    def process(
        self,
        user_input: str,
    ):

        self.conversation.add_user_message(
            user_input,
        )

        # ==========================================
        # MEMORY INTELLIGENCE
        # ==========================================

        facts = self.memory_ai.analyze(
            user_input,
        )
        logger.info(
            "==================================================\n"
            "MEMORY INTELLIGENCE\n"
            "==================================================\n\n"
            "Facts encontrados: {}\n\n{}",
            len(facts),
            "\n".join(f"{fact.key} = {fact.value}" for fact in facts),
        )

        for fact in facts:
            self.memory.remember(
                fact.key,
                fact.value,
            )

        logger.info(
            "==================================================\n"
            "LONG TERM MEMORY\n"
            "==================================================\n\n{}",
            "\n".join(
                f"{memory.key} = {memory.value}" for memory in self.memory.knowledge()
            )
            or "<sin memorias>",
        )

        # ==========================================
        # DECISION
        # ==========================================

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

        logger.info(
            "==================================================\n"
            "BUILDING CONTEXT\n"
            "==================================================",
        )
        context = self.context.build_context(
            user_input,
        )
        logger.info(
            "==================================================\n"
            "CONTEXT CREATED\n"
            "==================================================\n\n"
            "Conversation:\n{}\n\n"
            "Memories:\n{}\n\n"
            "Knowledge:\n{}",
            len(context.conversation),
            len(context.memories),
            len(context.knowledge),
        )

        # ==========================================
        # PROMPT
        # ==========================================

        logger.info(
            "==================================================\n"
            "BUILDING PROMPT\n"
            "==================================================",
        )
        prompt = self.prompt.build_prompt(
            intent=decision.intent,
            context=context,
            user_input=user_input,
        )
        logger.info(
            "==================================================\n"
            "PROMPT READY\n"
            "==================================================\n\n"
            "Longitud del prompt: {} caracteres.",
            len(prompt),
        )

        # ==========================================
        # MODELO
        # ==========================================

        logger.info(
            "==================================================\n"
            "CALLING LLM\n"
            "==================================================",
        )
        model_response = self.models.chat(
            prompt,
        )

        response = Response(
            content=model_response,
            response_type=ResponseType.TEXT,
        )

        processed = self.response.process(
            response,
        )

        # ==========================================
        # REFLECTION
        # ==========================================

        reflection = self.reflection.reflect(
            question=user_input,
            answer=processed.content,
        )

        if reflection.status == ReflectionStatus.REJECTED:
            processed.content = "No pude generar una respuesta confiable."

        self.conversation.add_assistant_message(
            processed.content,
        )

        return processed.content

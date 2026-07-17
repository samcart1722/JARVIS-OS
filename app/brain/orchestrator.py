from app.core.container import container
from app.handlers.memory_handler import MemoryHandler
from app.reasoning.engine import ReasoningEngine


class Orchestrator:
    def __init__(self):

        self.memory = container.memory

        self.memory_handler = MemoryHandler()

        self.reasoning = ReasoningEngine()

    def process(
        self,
        user_input: str,
    ):

        # ==========================================
        # Guardar conversación
        # ==========================================

        self.memory.remember_conversation(
            "user",
            user_input,
        )

        # ==========================================
        # Guardar memoria permanente
        # ==========================================

        memory_response = self.memory_handler.handle(
            user_input,
        )

        if memory_response:
            return memory_response

        # ==========================================
        # Todo el razonamiento ocurre aquí
        # ==========================================

        return self.reasoning.process(
            user_input,
        )

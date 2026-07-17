from app.context.builder import ContextBuilder
from app.context.models import Context
from app.memory.manager import MemoryManager


class ContextManager:
    """
    Coordina únicamente la construcción
    del contexto utilizado por JARVIS.
    """

    def __init__(
        self,
        memory: MemoryManager,
    ):

        self.builder = ContextBuilder(
            memory,
        )

    def build_context(
        self,
        user_input: str,
    ) -> Context:

        return self.builder.build(
            user_input,
        )
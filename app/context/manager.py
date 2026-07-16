from app.context.builder import ContextBuilder
from app.context.prompt_builder import PromptBuilder
from app.memory.manager import MemoryManager


class ContextManager:
    """
    Coordina la construcción del contexto
    y del prompt final.
    """

    def __init__(
        self,
        memory: MemoryManager,
    ):

        self.builder = ContextBuilder(
            memory,
        )

        self.prompt_builder = PromptBuilder()

    def build_prompt(
        self,
        user_input: str,
    ) -> str:

        context = self.builder.build(
            user_input,
        )

        return self.prompt_builder.build(
            context,
            user_input,
        )
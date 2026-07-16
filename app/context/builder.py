from app.context.models import Context
from app.context.providers import MemoryProvider
from app.memory.manager import MemoryManager


class ContextBuilder:
    """
    Construye el contexto completo
    para el motor cognitivo.
    """

    def __init__(
        self,
        memory: MemoryManager,
    ):

        self.providers = [

            MemoryProvider(
                memory,
            ),

        ]

    def build(
        self,
        user_input: str,
    ) -> Context:

        context = Context()

        for provider in self.providers:

            data = provider.provide(
                user_input,
            )

            context.conversation.extend(
                data.get(
                    "conversation",
                    [],
                )
            )

            context.memories.extend(
                data.get(
                    "memory",
                    [],
                )
            )

        return context
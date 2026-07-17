from app.context.models import Context
from app.context.providers import ConversationProvider, MemoryProvider
from app.conversation.manager import ConversationManager
from app.memory.manager import MemoryManager


class ContextBuilder:
    """
    Construye el contexto completo
    para el motor cognitivo.
    """

    def __init__(
        self,
        memory: MemoryManager,
        conversation: ConversationManager,
    ):

        self.providers = [
            ConversationProvider(
                conversation,
            ),
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

            context.knowledge.extend(
                data.get(
                    "knowledge",
                    [],
                )
            )

            profile = data.get(
                "profile",
            )

            if profile:
                context.profile.update(
                    profile,
                )

            metadata = data.get(
                "metadata",
            )

            if metadata:
                context.metadata.update(
                    metadata,
                )

        return context

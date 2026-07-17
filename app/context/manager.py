from app.context.builder import ContextBuilder
from app.context.models import Context
from app.conversation.manager import ConversationManager
from app.memory.manager import MemoryManager


class ContextManager:
    """
    Coordina la construcción del contexto
    utilizado por JARVIS.
    """

    def __init__(
        self,
        memory: MemoryManager,
        conversation: ConversationManager,
    ):

        self.builder = ContextBuilder(
            memory=memory,
            conversation=conversation,
        )

    def build_context(
        self,
        user_input: str,
    ) -> Context:

        return self.builder.build(
            user_input,
        )

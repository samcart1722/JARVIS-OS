from abc import ABC, abstractmethod

from app.conversation.manager import ConversationManager
from app.memory.manager import MemoryManager
from app.memory.retriever import MemoryRetriever


class ContextProvider(ABC):
    """
    Interfaz base para cualquier
    proveedor de contexto.
    """

    @abstractmethod
    def provide(
        self,
        user_input: str,
    ):
        pass


class MemoryProvider(ContextProvider):
    def __init__(
        self,
        memory: MemoryManager,
    ) -> None:
        self.retriever = MemoryRetriever(
            memory,
        )

    def provide(
        self,
        user_input: str,
    ) -> dict[str, list[dict[str, str]]]:

        memories = self.retriever.retrieve(
            user_input,
        )

        return {
            "memory": [
                {
                    "key": memory.key,
                    "value": memory.value,
                }
                for memory in memories
            ],
        }


class ConversationProvider(ContextProvider):
    def __init__(
        self,
        conversation: ConversationManager,
    ) -> None:
        self.conversation = conversation

    def provide(
        self,
        user_input: str,
    ) -> dict[str, list[dict[str, str]]]:

        return {
            "conversation": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in self.conversation.messages()
            ],
        }

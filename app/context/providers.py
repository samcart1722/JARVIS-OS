from abc import ABC, abstractmethod

from app.conversation.manager import ConversationManager
from app.memory.manager import MemoryManager


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
    ):

        self.memory = memory

    def provide(
        self,
        user_input: str,
    ):

        return {
            "memory": self.memory.knowledge(),
        }


class ConversationProvider(ContextProvider):
    def __init__(
        self,
        conversation: ConversationManager,
    ):

        self.conversation = conversation

    def provide(
        self,
        user_input: str,
    ):

        return {
            "conversation": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in self.conversation.messages()
            ],
        }

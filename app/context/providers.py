from abc import ABC, abstractmethod

from app.conversation.manager import ConversationManager
from app.memory.manager import MemoryManager
from app.memory.pipeline import MemoryPipeline


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
    """
    Proveedor de contexto basado en memoria.

    Utiliza el MemoryPipeline para recuperar,
    rankear, ordenar y seleccionar las memorias
    que formarán parte del contexto.
    """

    def __init__(
        self,
        memory: MemoryManager,
    ) -> None:
        self.pipeline = MemoryPipeline(
            memory,
        )

    def provide(
        self,
        user_input: str,
    ) -> dict[str, list[dict[str, str]]]:

        facts = self.pipeline.retrieve(
            user_input,
        )

        return {
            "memory": [
                {
                    "key": fact.key,
                    "value": fact.value,
                }
                for fact in facts
            ],
        }


class ConversationProvider(ContextProvider):
    """
    Proveedor del historial de conversación.
    """

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

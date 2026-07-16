from abc import ABC, abstractmethod

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

            "conversation": self.memory.conversation(),

            "memory": self.memory.knowledge(),

        }
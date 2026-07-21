from abc import ABC, abstractmethod

from app.context.models import Context


class PromptSection(ABC):
    """
    Contrato base para cualquier
    sección del prompt.
    """

    @abstractmethod
    def build(
        self,
        context: Context,
    ) -> str:
        """
        Construye la sección del prompt.

        Devuelve una cadena vacía cuando
        la sección no deba aparecer.
        """
        raise NotImplementedError

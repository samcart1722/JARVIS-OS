from abc import ABC, abstractmethod

from app.memory.intent import Intent


class IntentAnalyzer(ABC):
    """
    Contrato para cualquier analizador
    de intención del usuario.
    """

    @abstractmethod
    def analyze(
        self,
        user_input: str,
    ) -> Intent:
        """
        Analiza la solicitud del usuario
        y devuelve la intención detectada.
        """
        raise NotImplementedError

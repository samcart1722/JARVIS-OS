from app.reasoning.engine import ReasoningEngine


class ProfileHandler:
    """
    Adaptador temporal hacia la nueva arquitectura.

    La gestión del perfil del usuario será absorbida por
    el ReasoningEngine y los componentes de memoria
    durante la consolidación del Core.
    """

    def __init__(self):
        self.reasoning = ReasoningEngine()

    def handle(self, user_input: str):
        return self.reasoning.process(user_input)

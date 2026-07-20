from app.reasoning.engine import ReasoningEngine


class ChatHandler:
    """
    Adaptador temporal hacia la nueva arquitectura.

    Será eliminado cuando desaparezca definitivamente
    la capa de handlers.
    """

    def __init__(self):
        self.reasoning = ReasoningEngine()

    def handle(self, user_input: str):
        return self.reasoning.process(user_input)

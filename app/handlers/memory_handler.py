from app.reasoning.engine import ReasoningEngine


class MemoryHandler:
    """
    Adaptador temporal hacia la nueva arquitectura.

    La extracción y almacenamiento de memoria ya no se
    realiza desde este handler, sino desde el
    ReasoningEngine.
    """

    def __init__(self):
        self.reasoning = ReasoningEngine()

    def handle(self, user_input: str):
        return self.reasoning.process(user_input)

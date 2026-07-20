from app.reasoning.engine import ReasoningEngine


class Orchestrator:
    def __init__(self):
        self.reasoning = ReasoningEngine()

    def process(self, user_input: str):
        return self.reasoning.process(user_input)

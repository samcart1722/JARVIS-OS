from app.core.container import container


class Orchestrator:
    def __init__(self):
        self.cognitive_engine = container.cognitive_engine

    def process(self, user_input: str):
        return self.cognitive_engine.process(user_input)

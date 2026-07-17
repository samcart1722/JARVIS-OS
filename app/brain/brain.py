from app.brain.orchestrator import Orchestrator


class Brain:
    def __init__(self):
        self.orchestrator = Orchestrator()

    def think(self, user_input: str):

        return self.orchestrator.process(user_input)

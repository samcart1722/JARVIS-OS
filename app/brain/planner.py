from enum import Enum

from app.brain.intent_classifier import IntentClassifier


class TaskType(str, Enum):
    CHAT = "CHAT"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    AGENT = "AGENT"


class Planner:

    def __init__(self):
        self.classifier = IntentClassifier()

    def plan(self, user_input: str) -> TaskType:

        intent = self.classifier.classify(user_input)

        try:
            return TaskType(intent)

        except ValueError:
            return TaskType.CHAT
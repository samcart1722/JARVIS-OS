from enum import Enum


class TaskType(str, Enum):
    CHAT = "chat"
    TOOL = "tool"
    MEMORY = "memory"
    AGENT = "agent"


class Planner:

    def plan(self, user_input: str) -> TaskType:
        text = user_input.lower()

        if any(word in text for word in ["abre", "ejecuta", "busca"]):
            return TaskType.TOOL

        if any(word in text for word in ["recuerda", "memoria"]):
            return TaskType.MEMORY

        return TaskType.CHAT
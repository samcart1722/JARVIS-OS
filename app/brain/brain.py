from app.brain.planner import Planner, TaskType
from app.tools.manager import ToolManager
from app.models.ollama_client import OllamaClient


class Brain:

    def __init__(self):
        self.planner = Planner()
        self.tools = ToolManager()
        self.ollama = OllamaClient()

    def think(self, user_input: str):

        task = self.planner.plan(user_input)

        if task == TaskType.CHAT:
            return self.ollama.chat(user_input)

        if task == TaskType.TOOL:
            return self.tools.execute("general")

        if task == TaskType.MEMORY:
            return "Necesito consultar la memoria."

        return "No sé cómo resolver esta tarea todavía."
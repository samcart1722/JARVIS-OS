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

            text = user_input.lower()

            if "visual studio" in text or "vscode" in text:
                return self.tools.execute("windows", "vscode")

            if "bloc" in text or "notepad" in text:
                return self.tools.execute("windows", "notepad")

            if "calculadora" in text or "calculator" in text:
                return self.tools.execute("windows", "calculator")

            if "explorador" in text or "explorer" in text:
                return self.tools.execute("windows", "explorer")

            return "No sé qué aplicación deseas abrir."

        if task == TaskType.MEMORY:
            return "Necesito consultar la memoria."

        return "No sé cómo resolver esta tarea todavía."
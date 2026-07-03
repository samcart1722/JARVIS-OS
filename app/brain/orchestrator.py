from app.brain.planner import Planner, TaskType
from app.models.ollama_client import OllamaClient
from app.tools.manager import ToolManager


class Orchestrator:

    def __init__(self):
        self.planner = Planner()
        self.ollama = OllamaClient()
        self.tools = ToolManager()

    def process(self, user_input: str):

        task = self.planner.plan(user_input)

        if task == TaskType.CHAT:
            return self.ollama.chat(user_input)

        if task == TaskType.TOOL:

            text = user_input.lower()

            if "visual studio" in text or "vscode" in text:
                return self.tools.execute("windows", "vscode")

            if "calculadora" in text:
                return self.tools.execute("windows", "calculator")

            if "bloc" in text or "notepad" in text:
                return self.tools.execute("windows", "notepad")

            if "explorador" in text:
                return self.tools.execute("windows", "explorer")

            return "No sé qué aplicación deseas abrir."

        if task == TaskType.MEMORY:
            return "La memoria todavía no está implementada."

        return "No puedo procesar esa solicitud."
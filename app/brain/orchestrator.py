from app.brain.planner import Planner, TaskType
from app.brain.memory_rules import MemoryRules

from app.models.manager import ModelManager

from app.tools.manager import ToolManager

from app.memory.manager import MemoryManager
from app.memory.extractor import MemoryExtractor


class Orchestrator:

    def __init__(self):

        self.planner = Planner()

        self.model = ModelManager()

        self.tools = ToolManager()

        self.memory = MemoryManager()

        self.memory_rules = MemoryRules()

        self.extractor = MemoryExtractor()

    def process(self, user_input: str):

        # Guardar conversación
        self.memory.remember_conversation(
            "user",
            user_input,
        )

        # Guardar memoria importante
        if self.memory_rules.should_store(user_input):

            item = self.extractor.extract(user_input)

            if item is not None:

                self.memory.remember(
                    item.key,
                    item.value,
                )

                return (
    f"Entendido. Recordaré que tu "
    f"{item.label} es {item.value}."
)

        # Consultar memoria

        if "cual es mi proyecto principal" in user_input.lower():

            project = self.memory.recall("project")

            if project:

                return (
                    f"Tu proyecto principal es {project}."
                )

            return (
                "Todavía no conozco tu proyecto principal."
            )

        task = self.planner.plan(user_input)

        if task == TaskType.CHAT:

            response = self.model.chat(user_input)

            self.memory.remember_conversation(
                "assistant",
                response,
            )

            return response

        if task == TaskType.TOOL:

            text = user_input.lower()

            if "visual studio" in text or "vscode" in text:
                return self.tools.execute(
                    "windows",
                    "vscode",
                )

            if "calculadora" in text:
                return self.tools.execute(
                    "windows",
                    "calculator",
                )

            if "bloc" in text or "notepad" in text:
                return self.tools.execute(
                    "windows",
                    "notepad",
                )

            if "explorador" in text:
                return self.tools.execute(
                    "windows",
                    "explorer",
                )

            return "No sé qué aplicación deseas abrir."

        if task == TaskType.MEMORY:
            return "La memoria todavía no está implementada."

        return "No puedo procesar esa solicitud."
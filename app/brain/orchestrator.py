from app.brain.planner import TaskType
from app.core.container import container
from app.handlers.browser_handler import BrowserHandler
from app.handlers.chat_handler import ChatHandler
from app.handlers.memory_handler import MemoryHandler
from app.handlers.profile_handler import ProfileHandler
from app.handlers.tool_handler import ToolHandler
from app.reasoning.engine import ReasoningEngine


class Orchestrator:

    def __init__(self):

        self.planner = container.planner

        self.memory = container.memory

        self.chat = ChatHandler()

        self.tools = ToolHandler()

        self.memory_handler = MemoryHandler()

        self.profile = ProfileHandler()

        self.browser = BrowserHandler()

        self.reasoning = ReasoningEngine()
        
    def process(self, user_input: str):

        # Guardar conversación del usuario
        self.memory.remember_conversation(
            "user",
            user_input,
        )

        # ==========================
        # Consultas al perfil
        # ==========================

        if "que proyectos tengo" in user_input.lower():

            return self.profile.handle()

        # ==========================
        # Consultas de memoria
        # ==========================

        if "cual es mi proyecto principal" in user_input.lower():

            project = self.memory.recall("project")

            if project:

                return f"Tu proyecto principal es {project}."

            return "Todavía no conozco tu proyecto principal."

        # ==========================
        # Guardado de memoria
        # ==========================

        memory_response = self.memory_handler.handle(user_input)

        if memory_response:

            return memory_response

        # ==========================
        # Planificación
        # ==========================

        task = self.planner.plan(user_input)

        if task == TaskType.CHAT:

            return self.chat.handle(user_input)

        if task == TaskType.TOOL:

            return self.tools.handle(user_input)

        if task == TaskType.BROWSER:

            return self.browser.handle(user_input)

        return "No puedo procesar esa solicitud."
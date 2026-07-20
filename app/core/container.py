from app.context.manager import ContextManager
from app.conversation.manager import ConversationManager
from app.knowledge.manager import KnowledgeManager
from app.memory.manager import MemoryManager
from app.models.manager import ModelManager
from app.prompt.manager import PromptManager
from app.reasoning.rules import ReasoningRules
from app.reflection.engine import ReflectionEngine
from app.response.manager import ResponseManager
from app.tools.manager import ToolManager


class ServiceContainer:
    """
    Contenedor principal de servicios
    de JARVIS.
    """

    def __init__(self):

        # Conversation
        self.conversation = ConversationManager()

        # Memory
        self.memory = MemoryManager()

        # Knowledge
        self.knowledge = KnowledgeManager()

        # Context
        self.context = ContextManager(
            memory=self.memory,
            conversation=self.conversation,
        )

        # Prompt
        self.prompt = PromptManager()

        # Tools
        self.tools = ToolManager()

        # Models
        self.models = ModelManager()

        # Reflection
        self.reflection = ReflectionEngine()

        # Response
        self.response = ResponseManager()

        # Rules
        self.rules = ReasoningRules()


container = ServiceContainer()

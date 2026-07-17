from app.brain.memory_rules import MemoryRules
from app.brain.planner import Planner
from app.context.manager import ContextManager
from app.knowledge.manager import KnowledgeManager
from app.memory.extractor import MemoryExtractor
from app.memory.manager import MemoryManager
from app.models.manager import ModelManager
from app.profile.manager import ProfileManager
from app.prompt.manager import PromptManager
from app.tools.manager import ToolManager


class ServiceContainer:

    def __init__(self):

        # ==========================
        # Brain
        # ==========================

        self.planner = Planner()

        # ==========================
        # Model
        # ==========================

        self.model = ModelManager()

        # ==========================
        # Memory
        # ==========================

        self.memory = MemoryManager()
        self.memory_extractor = MemoryExtractor()
        self.memory_rules = MemoryRules()

        # ==========================
        # Context
        # ==========================

        self.context = ContextManager(
            self.memory,
        )

        # ==========================
        # Prompt
        # ==========================

        self.prompt = PromptManager()

        # ==========================
        # Knowledge
        # ==========================

        self.knowledge = KnowledgeManager()

        # ==========================
        # Profile
        # ==========================

        self.profile = ProfileManager()

        # ==========================
        # Tools
        # ==========================

        self.tools = ToolManager()


container = ServiceContainer()
from app.brain.memory_rules import MemoryRules
from app.brain.planner import Planner
from app.knowledge.manager import KnowledgeManager
from app.memory.extractor import MemoryExtractor
from app.memory.manager import MemoryManager
from app.models.manager import ModelManager
from app.profile.manager import ProfileManager
from app.tools.manager import ToolManager


class ServiceContainer:

    def __init__(self):

        # Brain
        self.planner = Planner()

        # Model
        self.model = ModelManager()

        # Memory
        self.memory = MemoryManager()
        self.memory_extractor = MemoryExtractor()
        self.memory_rules = MemoryRules()

        # Knowledge
        self.knowledge = KnowledgeManager()

        # Profile
        self.profile = ProfileManager()

        # Tools
        self.tools = ToolManager()


container = ServiceContainer()

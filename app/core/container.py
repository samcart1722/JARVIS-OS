from app.models.manager import ModelManager

from app.memory.manager import MemoryManager
from app.memory.extractor import MemoryExtractor

from app.profile.manager import ProfileManager

from app.tools.manager import ToolManager

from app.brain.planner import Planner
from app.brain.memory_rules import MemoryRules


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

        # Profile
        self.profile = ProfileManager()

        # Tools
        self.tools = ToolManager()


container = ServiceContainer()
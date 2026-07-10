from app.brain.planner import TaskType

from app.handlers.chat_handler import ChatHandler
from app.handlers.tool_handler import ToolHandler
from app.handlers.memory_handler import MemoryHandler
from app.handlers.browser_handler import BrowserHandler


class HandlerRegistry:

    def __init__(self):

        self.handlers = {
            TaskType.CHAT: ChatHandler(),
            TaskType.TOOL: ToolHandler(),
            TaskType.MEMORY: MemoryHandler(),
            TaskType.BROWSER: BrowserHandler(),
        }

    def get(self, task):

        return self.handlers.get(task)
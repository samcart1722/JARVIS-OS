from app.tools.registry import ToolRegistry
from app.tools.windows import WindowsTool


class ToolManager:

    def __init__(self):

        self.registry = ToolRegistry()

        self.registry.register(
            "windows",
            WindowsTool(),
        )

    def execute(self, tool_name: str, command: str):

        tool = self.registry.get(tool_name)

        if tool is None:
            return f"Herramienta '{tool_name}' no encontrada."

        return tool.open_application(command)
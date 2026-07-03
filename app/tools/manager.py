from app.tools.windows import WindowsTool


class ToolManager:

    def __init__(self):
        self.windows = WindowsTool()

    def execute(self, tool_name: str, command: str = ""):

        if tool_name == "windows":
            return self.windows.open_application(command)

        return f"Herramienta desconocida: {tool_name}"
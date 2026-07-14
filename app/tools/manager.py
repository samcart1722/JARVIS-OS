from app.tools.browser import BrowserTool
from app.tools.windows import WindowsTool


class ToolManager:

    def __init__(self):

        self.windows = WindowsTool()

        self.browser = BrowserTool()

    def execute(
        self,
        tool_name: str,
        command: str = "",
    ):

        if tool_name == "windows":
            return self.windows.open_application(command)

        if tool_name == "browser":
            return self.browser.search(command)

        return f"Herramienta desconocida: {tool_name}"
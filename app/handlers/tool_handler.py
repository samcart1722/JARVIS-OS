from app.core.container import container


class ToolHandler:

    def __init__(self):

        self.tools = container.tools

    def handle(self, user_input: str):

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
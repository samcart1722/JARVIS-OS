from app.core.container import container


class BrowserHandler:

    def __init__(self):

        self.tools = container.tools

    def handle(self, query: str):

        return self.tools.execute(
            "browser",
            query,
        )
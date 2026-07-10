from app.core.container import container


class BrowserHandler:

    def __init__(self):

        self.tools = container.tools

        self.model = container.model

    def handle(self, query: str):

        results = self.tools.execute(
            "browser",
            query,
        )

        prompt = (
            "Resume la siguiente información obtenida "
            "de una búsqueda web:\n\n"
            f"{results}"
        )

        return self.model.chat(prompt)
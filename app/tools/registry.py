class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name: str, tool):

        self.tools[name] = tool

    def get(self, name: str):

        return self.tools.get(name)
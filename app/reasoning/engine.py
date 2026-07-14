from app.core.container import container
from app.reasoning.models import ActionType
from app.reasoning.rules import ReasoningRules


class ReasoningEngine:

    def __init__(self):

        self.rules = ReasoningRules()

        self.memory = container.memory

        self.knowledge = getattr(container, "knowledge", None)

        self.tools = container.tools

        self.model = container.model

    def process(
        self,
        user_input: str,
    ):

        decision = self.rules.decide(user_input)

        # ----------------------------
        # MEMORY
        # ----------------------------

        if decision.action == ActionType.MEMORY:

            project = self.memory.recall("project")

            if project:

                return project

            return "No encontré información en la memoria."

        # ----------------------------
        # KNOWLEDGE
        # ----------------------------

        if decision.action == ActionType.KNOWLEDGE:

            if self.knowledge:

                return "Knowledge Engine disponible."

            return "Knowledge Engine no disponible."

        # ----------------------------
        # TOOLS
        # ----------------------------

        if decision.action == ActionType.TOOL:

            return self.tools.execute(user_input)

        # ----------------------------
        # BROWSER
        # ----------------------------

        if decision.action == ActionType.BROWSER:

            return self.model.generate(
                "Utiliza BrowserTool para responder: "
                + user_input
            )

        # ----------------------------
        # MODEL
        # ----------------------------

        return self.model.generate(user_input)
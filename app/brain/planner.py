from enum import Enum


class TaskType(str, Enum):
    CHAT = "CHAT"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    BROWSER = "BROWSER"
    AGENT = "AGENT"


class Planner:

    def plan(self, user_input: str) -> TaskType:

        text = user_input.lower()

        # Browser
        if any(
            word in text
            for word in [
                "busca",
                "buscar",
                "investiga",
                "consulta",
            ]
        ):
            return TaskType.BROWSER

        # Herramientas de Windows
        if any(
            word in text
            for word in [
                "abre",
                "ejecuta",
                "inicia",
            ]
        ):
            return TaskType.TOOL

        # Memoria
        if any(
            word in text
            for word in [
                "recuerda",
                "mi proyecto",
                "mi nombre",
                "mi empresa",
            ]
        ):
            return TaskType.MEMORY

        return TaskType.CHAT
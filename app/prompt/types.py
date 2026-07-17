from enum import Enum


class PromptType(str, Enum):
    """
    Tipos de prompts que JARVIS puede construir.

    Cada tipo representa una estrategia distinta
    para comunicarse con el modelo de lenguaje.
    """

    GENERAL = "general"

    CODING = "coding"

    MEDICAL = "medical"

    RESEARCH = "research"

    BROWSER = "browser"

    PLANNING = "planning"

    SYSTEM = "system"
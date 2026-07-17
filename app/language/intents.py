from enum import Enum


class Intent(str, Enum):
    """
    Lenguaje interno de JARVIS.

    Todas las decisiones del sistema deberán
    expresarse mediante una intención.
    """

    # ==========================
    # General
    # ==========================

    GENERAL_CHAT = "GENERAL_CHAT"

    # ==========================
    # Memory
    # ==========================

    PERSONAL_MEMORY = "PERSONAL_MEMORY"

    SAVE_MEMORY = "SAVE_MEMORY"

    PROJECT_QUERY = "PROJECT_QUERY"

    PROJECT_LIST = "PROJECT_LIST"

    PROFILE_QUERY = "PROFILE_QUERY"

    # ==========================
    # Knowledge
    # ==========================

    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"

    KNOWLEDGE_LEARN = "KNOWLEDGE_LEARN"

    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"

    # ==========================
    # Browser
    # ==========================

    WEB_SEARCH = "WEB_SEARCH"

    NEWS_SEARCH = "NEWS_SEARCH"

    # ==========================
    # Tools
    # ==========================

    TOOL_EXECUTION = "TOOL_EXECUTION"

    APPLICATION_OPEN = "APPLICATION_OPEN"

    # ==========================
    # Future
    # ==========================

    OCR_READ = "OCR_READ"

    VISION_ANALYSIS = "VISION_ANALYSIS"

    SPEECH_COMMAND = "SPEECH_COMMAND"

    MEDICAL_REASONING = "MEDICAL_REASONING"

    FINANCE_ANALYSIS = "FINANCE_ANALYSIS"

    AUTOMATION = "AUTOMATION"

    AGENT_TASK = "AGENT_TASK"

from app.language.intents import Intent

INTENT_SYNONYMS = {
    # ==========================================
    # Personal Memory
    # ==========================================
    Intent.PERSONAL_MEMORY: [
        "cual es mi proyecto",
        "cual es mi proyecto principal",
        "proyecto principal",
        "cual es mi profesion",
        "mi profesion",
        "como me llamo",
        "cual es mi nombre",
        "donde vivo",
        "cual es mi empresa",
    ],
    # ==========================================
    # Project List
    # ==========================================
    Intent.PROJECT_LIST: [
        "que proyectos tengo",
        "mis proyectos",
        "proyectos",
        "en que estoy trabajando",
        "proyectos activos",
    ],
    # ==========================================
    # Knowledge
    # ==========================================
    Intent.KNOWLEDGE_QUERY: [
        "que sabes sobre",
        "que conozco sobre",
        "muestrame",
        "explicame",
        "hablame de",
    ],
    # ==========================================
    # Web
    # ==========================================
    Intent.WEB_SEARCH: [
        "busca",
        "buscar",
        "investiga",
        "consulta",
        "ultimas noticias",
        "novedades",
    ],
    # ==========================================
    # Tools
    # ==========================================
    Intent.TOOL_EXECUTION: [
        "abre",
        "ejecuta",
        "inicia",
    ],
}

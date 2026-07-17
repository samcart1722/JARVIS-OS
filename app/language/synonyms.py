from app.language.intents import Intent

INTENT_SYNONYMS = {
    Intent.PROJECT_QUERY: [
        "cual es mi proyecto",
        "cual es mi proyecto principal",
        "proyecto principal",
    ],
    Intent.PROJECT_LIST: [
        "que proyectos tengo",
        "mis proyectos",
        "proyectos",
        "en que estoy trabajando",
        "proyectos activos",
    ],
    Intent.KNOWLEDGE_QUERY: [
        "que sabes sobre",
        "que conozco sobre",
        "muestrame",
        "explicame",
        "hablame de",
    ],
    Intent.WEB_SEARCH: [
        "busca",
        "buscar",
        "investiga",
        "consulta",
        "ultimas noticias",
        "novedades",
    ],
    Intent.TOOL_EXECUTION: [
        "abre",
        "ejecuta",
        "inicia",
    ],
}

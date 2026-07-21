from app.memory.intent import Intent
from app.memory.intent_analyzer import IntentAnalyzer


class KeywordIntentAnalyzer(IntentAnalyzer):
    """
    Analizador de intención basado
    en palabras clave.
    """

    TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
        "project": (
            "proyecto",
            "plataforma",
            "app",
            "aplicación",
            "sistema",
            "software",
        ),
        "backend": (
            "backend",
            "api",
            "servidor",
        ),
        "medical": (
            "hospital",
            "paciente",
            "médico",
            "doctor",
            "consulta",
            "clínica",
        ),
    }

    def analyze(
        self,
        user_input: str,
    ) -> Intent:

        text = user_input.lower()

        topics: list[str] = []

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                topics.append(
                    topic,
                )

        return Intent(
            topics=topics,
            confidence=1.0,
        )

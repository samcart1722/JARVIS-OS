from app.memory.facts import MemoryFact


class MemoryExtractor:
    """
    Extractor básico de memorias.

    Conserva compatibilidad con el pipeline anterior mientras
    toda la extracción migra al sistema de extractores
    especializados.
    """

    def extract(
        self,
        text: str,
    ) -> MemoryFact | None:

        text_lower = text.lower()

        if "mi proyecto principal es" in text_lower:
            value = text.split("es", 1)[1].strip()

            return MemoryFact(
                key="project",
                value=value,
            )

        return None

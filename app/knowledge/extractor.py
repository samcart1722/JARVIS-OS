import re

from app.knowledge.models import KnowledgeUnit


class KnowledgeExtractor:
    """
    Primera versión del extractor.

    En esta etapa NO usamos IA.

    Simplemente detectamos conceptos
    relevantes mediante reglas.

    Más adelante este componente será
    reemplazado por un extractor basado
    en modelos de lenguaje.
    """

    def extract(
        self,
        unit: KnowledgeUnit,
    ) -> list[str]:

        text = f"{unit.title} {unit.content}"

        words = re.findall(
            r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\-]+",
            text,
        )

        concepts = []

        for word in words:
            if len(word) < 4:
                continue

            if word.lower() in [
                "para",
                "como",
                "este",
                "esta",
                "sobre",
                "entre",
                "desde",
                "hasta",
                "porque",
                "donde",
                "cuando",
                "tambien",
                "tener",
            ]:
                continue

            if word not in concepts:
                concepts.append(word)

        return concepts

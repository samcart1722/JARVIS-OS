from app.knowledge.collector import KnowledgeCollector
from app.knowledge.extractor import KnowledgeExtractor
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.storage import KnowledgeStorage


class KnowledgeManager:

    def __init__(self):

        self.collector = KnowledgeCollector()

        self.extractor = KnowledgeExtractor()

        self.graph = KnowledgeGraph()

        self.storage = KnowledgeStorage()

    # =====================================================
    # Public API
    # =====================================================

    def answer(self, question: str):

        """
        Punto único de entrada para consultas al Knowledge Engine.
        """

        related = self.related(question)

        if related:

            return related

        return "No encontré conocimiento relacionado."

    def learn(
        self,
        title: str,
        content: str,
        source: str = "Manual",
        category: str = "General",
        tags=None,
    ):

        unit = self.collector.create(
            title=title,
            content=content,
            source=source,
            category=category,
            tags=tags,
        )

        concepts = self.extractor.extract(unit)

        for concept in concepts:

            self.graph.connect(
                unit.title,
                concept,
            )

        self.storage.save(unit)

        return unit

    def related(self, concept: str):

        return self.graph.related_to(concept)

    # Compatibilidad temporal

    def related_to(self, concept: str):

        return self.related(concept)
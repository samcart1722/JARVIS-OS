from app.knowledge.collector import KnowledgeCollector
from app.knowledge.storage import KnowledgeStorage


class KnowledgeManager:

    def __init__(self):

        self.collector = KnowledgeCollector()

        self.storage = KnowledgeStorage()

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

        self.storage.save(unit)

        return unit
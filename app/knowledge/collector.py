from app.knowledge.models import KnowledgeUnit


class KnowledgeCollector:
    def create(
        self,
        title: str,
        content: str,
        source: str = "Manual",
        category: str = "General",
        tags: list[str] | None = None,
    ) -> KnowledgeUnit:

        if tags is None:
            tags = []

        summary = content

        if len(summary) > 300:
            summary = summary[:300] + "..."

        return KnowledgeUnit(
            title=title,
            summary=summary,
            content=content,
            source=source,
            category=category,
            tags=tags,
        )

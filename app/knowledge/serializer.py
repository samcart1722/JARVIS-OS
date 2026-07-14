from app.knowledge.models import KnowledgeUnit


class KnowledgeSerializer:

    def to_markdown(
        self,
        unit: KnowledgeUnit,
    ) -> str:

        return f"""# {unit.title}

Source:
{unit.source}

Author:
{unit.author}

Category:
{unit.category}

Tags:
{", ".join(unit.tags)}

Created:
{unit.created_at}

Updated:
{unit.updated_at}

Confidence:
{unit.confidence}

Priority:
{unit.priority}

---

## Summary

{unit.summary}

---

## Content

{unit.content}
"""
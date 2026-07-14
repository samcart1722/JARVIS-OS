from pathlib import Path

from app.knowledge.models import KnowledgeUnit


class KnowledgeStorage:

    def __init__(self):

        self.base_path = Path("knowledge")

        self.base_path.mkdir(
            exist_ok=True,
        )

    def save(
        self,
        unit: KnowledgeUnit,
    ):

        category = unit.category.lower().replace(" ", "_")

        folder = self.base_path / category

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = (
            unit.title.lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        filepath = folder / f"{filename}.md"

        content = f"""# {unit.title}

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

        filepath.write_text(
            content,
            encoding="utf-8",
        )

        return filepath
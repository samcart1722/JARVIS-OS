from app.memory.models import MemoryItem


class MemoryExtractor:

    def extract(self, text: str):

        text_lower = text.lower()

        if "mi proyecto principal es" in text_lower:

            value = text.split("es", 1)[1].strip()

            return MemoryItem(
                key="project",
                value=value,
            )

        return None
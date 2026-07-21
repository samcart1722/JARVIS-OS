from app.memory.extractors.base import BaseMemoryExtractor
from app.memory.facts import MemoryFact


class ProjectExtractor(BaseMemoryExtractor):
    def extract(
        self,
        text: str,
        original: str,
    ) -> list[MemoryFact]:

        facts: list[MemoryFact] = []

        if "mi proyecto principal es" not in text:
            return facts

        value = original.split(
            "es",
            1,
        )[1].strip()

        if value:
            facts.append(
                MemoryFact(
                    key="project",
                    value=value,
                )
            )

        return facts

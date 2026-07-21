from app.memory.extractors.base import BaseMemoryExtractor
from app.memory.facts import MemoryFact


class ProfessionExtractor(BaseMemoryExtractor):
    def extract(
        self,
        text: str,
        original: str,
    ) -> list[MemoryFact]:

        facts: list[MemoryFact] = []

        if not text.startswith("soy "):
            return facts

        value = original.split(
            " ",
            1,
        )[1].strip()

        if value:
            facts.append(
                MemoryFact(
                    key="profession",
                    value=value,
                )
            )

        return facts

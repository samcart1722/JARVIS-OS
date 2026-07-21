from app.language.normalizer import TextNormalizer
from app.memory.facts import MemoryFact
from app.memory.registry import MEMORY_EXTRACTORS


class MemoryIntelligence:
    def __init__(
        self,
    ):

        self.normalizer = TextNormalizer()

    def analyze(
        self,
        user_input: str,
    ) -> list[MemoryFact]:

        facts: list[MemoryFact] = []

        text = self.normalizer.normalize(
            user_input,
        )

        for extractor_cls in MEMORY_EXTRACTORS:
            extractor = extractor_cls()

            facts.extend(
                extractor.extract(
                    text=text,
                    original=user_input,
                )
            )

        return facts

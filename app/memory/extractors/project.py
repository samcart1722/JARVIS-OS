from app.language.normalizer import TextNormalizer
from app.memory.extractors.base import BaseMemoryExtractor
from app.memory.facts import MemoryFact


class ProjectExtractor(BaseMemoryExtractor):
    PATTERNS: tuple[str, ...] = (
        "mi proyecto principal es",
        "mi proyecto es",
        "estoy construyendo",
        "estoy desarrollando",
        "estoy creando",
        "estoy trabajando en",
        "trabajo en",
        "desarrollo",
        "construyo",
        "creo",
    )

    def __init__(
        self,
    ) -> None:
        self.normalizer = TextNormalizer()

    def extract(
        self,
        text: str,
        original: str,
    ) -> list[MemoryFact]:

        normalized_text = self.normalizer.normalize(
            text,
        )

        for pattern in self.PATTERNS:
            if not normalized_text.startswith(pattern):
                continue

            value = (
                " ".join(original.split()[len(pattern.split()) :])
                .strip()
                .rstrip(".,;:!?")
            )

            if value:
                return [
                    MemoryFact(
                        key="project",
                        value=value,
                    )
                ]

        return []

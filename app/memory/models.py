from dataclasses import dataclass


@dataclass
class MemoryItem:
    key: str

    value: str

    @property
    def label(self) -> str:

        labels = {
            "project": "proyecto principal",
        }

        return labels.get(self.key, self.key)

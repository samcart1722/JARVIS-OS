from app.memory.facts import MemoryFact


class LongTermMemory:
    def __init__(self) -> None:
        self.memory: dict[str, MemoryFact] = {}

    def save(
        self,
        fact: MemoryFact,
    ) -> None:

        self.memory[fact.key] = fact

    def get(
        self,
        key: str,
    ) -> MemoryFact | None:

        return self.memory.get(key)

    def all(
        self,
    ) -> list[MemoryFact]:

        return list(self.memory.values())

    def clear(
        self,
    ) -> None:

        self.memory.clear()

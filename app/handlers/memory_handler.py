from app.core.container import container


class MemoryHandler:
    def __init__(self):

        self.memory = container.memory

        self.extractor = container.memory_extractor

        self.rules = container.memory_rules

        self.profile = container.profile

    def handle(self, user_input: str):

        if not self.rules.should_store(user_input):
            return None

        item = self.extractor.extract(user_input)

        if item is None:
            return None

        self.memory.remember(
            item.key,
            item.value,
        )

        self.profile.update_from_memory(item)

        return f"Entendido. Recordaré que tu {item.label} es {item.value}."

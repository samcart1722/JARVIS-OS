class MemoryRules:
    def should_store(self, text: str) -> bool:

        text = text.lower()

        rules = [
            "mi proyecto",
            "recuerda que",
            "mi nombre es",
            "trabajo en",
            "prefiero",
        ]

        return any(rule in text for rule in rules)

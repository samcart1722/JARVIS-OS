from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory


class MemoryManager:

    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    # ==========================
    # Short Term Memory
    # ==========================

    def remember_conversation(self, role: str, content: str):

        self.short_term.add(role, content)

    def conversation(self):

        return self.short_term.get_history()

    def clear_conversation(self):

        self.short_term.clear()

    # ==========================
    # Long Term Memory
    # ==========================

    def remember(self, key: str, value: str):

        self.long_term.save(key, value)

    def recall(self, key: str):

        return self.long_term.get(key)

    def knowledge(self):

        return self.long_term.all()

    def clear_memory(self):

        self.long_term.clear()
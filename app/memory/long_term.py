class LongTermMemory:

    def __init__(self):
        self.memory = {}

    def save(self, key: str, value: str):

        self.memory[key] = value

    def get(self, key: str):

        return self.memory.get(key)

    def all(self):

        return self.memory

    def clear(self):

        self.memory.clear()
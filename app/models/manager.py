from app.models.ollama_client import OllamaClient


class ModelManager:
    def __init__(self):
        self.ollama = OllamaClient()

    def generate(self, prompt: str) -> str:
        return self.ollama.chat(prompt)

    def chat(self, prompt: str) -> str:
        return self.generate(prompt)

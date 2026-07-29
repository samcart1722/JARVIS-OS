from app.models.ollama_client import OllamaClient


class ModelManager:
    def __init__(self, ollama: OllamaClient) -> None:
        self.ollama = ollama

    def generate(self, prompt: str) -> str:
        return self.ollama.chat(prompt)

    def chat(self, prompt: str) -> str:
        return self.generate(prompt)

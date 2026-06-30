import requests


class OllamaClient:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama3.2:3b"

    def chat(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]
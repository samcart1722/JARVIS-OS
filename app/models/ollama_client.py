import requests


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]

import json

from app.models.ollama_client import OllamaClient


class IntentClassifier:

    def __init__(self):
        self.model = OllamaClient()

    def classify(self, text: str) -> str:

        prompt = f"""
You are an intent classifier.

Return ONLY valid JSON.

Example:

{{
  "intent":"CHAT"
}}

Valid intents:

CHAT
TOOL
MEMORY
AGENT

User:

{text}
"""

        response = self.model.chat(prompt)

        try:

            data = json.loads(response)

            return data["intent"].upper()

        except Exception:

            return "CHAT"
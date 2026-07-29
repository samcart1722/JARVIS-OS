"""Ollama implementation of the cognitive reasoning provider."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.providers.base_provider import ReasoningProvider
from app.models.ollama_client import OllamaClient


class OllamaProvider(ReasoningProvider):
    """Generate reasoning results through the existing Ollama client."""

    def __init__(self) -> None:
        self._client = OllamaClient()

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        """Generate a response from the normalized user input."""
        response = self._client.chat(context.normalized_input)
        return ReasoningResult(response=response)

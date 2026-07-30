"""Ollama implementation of the cognitive reasoning provider."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.prompts.reasoning import ReasoningPromptBuilder
from app.cognition.providers.base_provider import ReasoningProvider
from app.models.ollama_client import OllamaClient


class OllamaProvider(ReasoningProvider):
    """Generate reasoning results through the existing Ollama client."""

    def __init__(
        self,
        client: OllamaClient,
        prompt_builder: ReasoningPromptBuilder,
    ) -> None:
        self._client = client
        self._prompt_builder = prompt_builder

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        """Generate a response from the normalized user input."""
        prompt = self._prompt_builder.build(context)
        response = self._client.chat(prompt)
        return ReasoningResult(response=response)

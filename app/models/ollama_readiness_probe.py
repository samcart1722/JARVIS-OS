"""Operational readiness implementation for Ollama."""

import requests

from app.models.ollama_client import OllamaClient
from app.operations.provider_readiness import (
    INVALID_RESPONSE,
    MODEL_UNAVAILABLE,
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessResult,
    readiness_result,
)


class OllamaReadinessProbe:
    """Check Ollama and its configured model through the non-generative API."""

    def __init__(self, client: OllamaClient) -> None:
        self._client = client

    def check(self) -> ProviderReadinessResult:
        """List models once and translate expected failures to safe states."""
        try:
            data = self._client.list_models()
        except requests.JSONDecodeError:
            return readiness_result(INVALID_RESPONSE)
        except requests.RequestException:
            return readiness_result(PROVIDER_UNAVAILABLE)

        try:
            models = data["models"]
            if not isinstance(models, list):
                raise TypeError
            if any(not isinstance(item, dict) for item in models):
                raise TypeError
            available = {
                identifier
                for item in models
                for identifier in (item.get("model"), item.get("name"))
                if isinstance(identifier, str)
            }
        except (KeyError, TypeError):
            return readiness_result(INVALID_RESPONSE)

        status = READY if self._client.model in available else MODEL_UNAVAILABLE
        return readiness_result(status)

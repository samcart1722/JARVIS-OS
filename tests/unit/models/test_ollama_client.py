"""Tests for explicitly configured Ollama infrastructure."""

from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.prompts.reasoning import (
    NormalizedInputReasoningPromptBuilder,
    ReasoningPromptBuilder,
)
from app.cognition.providers.ollama_provider import OllamaProvider
from app.models.ollama_client import OllamaClient


def configured_client() -> OllamaClient:
    return OllamaClient(
        base_url="http://ollama.test/api/generate",
        models_url="http://ollama.test/api/tags",
        model="test-model",
        timeout_seconds=15,
    )


def test_client_receives_configuration_without_network(monkeypatch) -> None:
    post = Mock()
    monkeypatch.setattr("app.models.ollama_client.requests.post", post)

    client = configured_client()

    assert client.url == "http://ollama.test/api/generate"
    assert client.model == "test-model"
    assert client.models_url == "http://ollama.test/api/tags"
    assert client.timeout_seconds == 15
    post.assert_not_called()


def test_client_uses_injected_configuration_when_chat_runs(
    monkeypatch,
) -> None:
    response = Mock()
    response.json.return_value = {"response": "Reasoned output"}
    post = Mock(return_value=response)
    monkeypatch.setattr("app.models.ollama_client.requests.post", post)

    result = configured_client().chat("Question")

    assert result == "Reasoned output"
    post.assert_called_once_with(
        "http://ollama.test/api/generate",
        json={
            "model": "test-model",
            "prompt": "Question",
            "stream": False,
        },
        timeout=15,
    )
    response.raise_for_status.assert_called_once_with()


def test_client_lists_models_with_one_non_generative_get(monkeypatch) -> None:
    response = Mock()
    response.json.return_value = {"models": []}
    get = Mock(return_value=response)
    monkeypatch.setattr("app.models.ollama_client.requests.get", get)

    result = configured_client().list_models()

    assert result == {"models": []}
    get.assert_called_once_with("http://ollama.test/api/tags", timeout=15)
    response.raise_for_status.assert_called_once_with()


def test_provider_uses_injected_client_and_returns_reasoning_result() -> None:
    client = Mock(spec=OllamaClient)
    client.chat.return_value = "Provider output"
    provider = OllamaProvider(
        client,
        NormalizedInputReasoningPromptBuilder(),
    )
    context = CognitiveContext(raw_input="Raw", normalized_input="Normalized")

    result = provider.generate(context)

    assert result == ReasoningResult(response="Provider output")
    client.chat.assert_called_once_with("Normalized")


def test_provider_builds_prompt_once_and_sends_exact_result() -> None:
    client = Mock(spec=OllamaClient)
    client.chat.return_value = "Provider output"
    prompt_builder = Mock(spec=ReasoningPromptBuilder)
    prompt_builder.build.return_value = "Structured prompt"
    provider = OllamaProvider(client, prompt_builder)
    context = CognitiveContext(raw_input="Raw", normalized_input="Normalized")

    result = provider.generate(context)

    assert result == ReasoningResult(response="Provider output")
    prompt_builder.build.assert_called_once_with(context)
    client.chat.assert_called_once_with("Structured prompt")


def test_provider_propagates_prompt_builder_error_without_client_call() -> None:
    client = Mock(spec=OllamaClient)
    prompt_builder = Mock(spec=ReasoningPromptBuilder)
    prompt_builder.build.side_effect = RuntimeError("controlled builder error")
    provider = OllamaProvider(client, prompt_builder)

    with pytest.raises(RuntimeError, match="controlled builder error"):
        provider.generate(CognitiveContext("Raw", "Normalized"))

    client.chat.assert_not_called()

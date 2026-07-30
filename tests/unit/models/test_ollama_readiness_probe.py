"""Tests for Ollama readiness without real network access."""

from unittest.mock import Mock

import pytest
import requests

from app.models.ollama_client import OllamaClient
from app.models.ollama_readiness_probe import OllamaReadinessProbe
from app.operations.provider_readiness import (
    INVALID_RESPONSE,
    MODEL_UNAVAILABLE,
    PROVIDER_UNAVAILABLE,
    READY,
)


def client() -> Mock:
    configured = Mock(spec=OllamaClient)
    configured.model = "llama3.2:3b"
    return configured


def test_construction_performs_no_network_or_model_listing() -> None:
    configured = client()

    OllamaReadinessProbe(configured)

    configured.list_models.assert_not_called()
    configured.chat.assert_not_called()


def test_check_lists_models_once_and_finds_model_by_model_field() -> None:
    configured = client()
    configured.list_models.return_value = {
        "models": [{"model": "llama3.2:3b", "name": "alias"}]
    }

    result = OllamaReadinessProbe(configured).check()

    assert result.status == READY
    configured.list_models.assert_called_once_with()
    configured.chat.assert_not_called()


def test_missing_model_is_distinct_from_provider_failure() -> None:
    configured = client()
    configured.list_models.return_value = {"models": [{"name": "other"}]}

    result = OllamaReadinessProbe(configured).check()

    assert result.status == MODEL_UNAVAILABLE
    configured.list_models.assert_called_once_with()


@pytest.mark.parametrize(
    "error",
    (
        requests.ConnectionError("internal host"),
        requests.Timeout("internal timeout"),
    ),
)
def test_transport_failure_is_safe_provider_unavailable(error) -> None:
    configured = client()
    configured.list_models.side_effect = error

    result = OllamaReadinessProbe(configured).check()

    assert result.status == PROVIDER_UNAVAILABLE
    assert "internal" not in result.message
    configured.list_models.assert_called_once_with()


@pytest.mark.parametrize(
    "payload",
    ({}, {"models": None}, {"models": "not-a-list"}, {"models": ["bad"]}),
)
def test_malformed_response_is_safe_invalid_response(payload) -> None:
    configured = client()
    configured.list_models.return_value = payload

    result = OllamaReadinessProbe(configured).check()

    assert result.status == INVALID_RESPONSE
    configured.list_models.assert_called_once_with()


def test_invalid_json_is_distinct_from_provider_unavailable() -> None:
    configured = client()
    configured.list_models.side_effect = requests.JSONDecodeError(
        "invalid", "secret response", 0
    )

    result = OllamaReadinessProbe(configured).check()

    assert result.status == INVALID_RESPONSE
    assert "secret response" not in result.message

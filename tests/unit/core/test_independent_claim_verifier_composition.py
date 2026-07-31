"""Sprint 20 settings and independent verifier composition tests."""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.cognition.grounding.claim_provider import ClaimEvidenceAttributionProvider
from app.cognition.grounding.provider import EvidenceBoundedReasoningProvider
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content


def settings(
    *, grounded=True, claim=True, verification=True, independent=False, **overrides
) -> Settings:
    values = {
        "MEMORY_GROUNDED_RESPONSE_ENABLED": grounded,
        "MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED": claim,
        "MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED": verification,
        "MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED": independent,
        **overrides,
    }
    return Settings(**values, _env_file=None)


def test_independent_settings_defaults_and_explicit_values_are_isolated() -> None:
    base = Settings(_env_file=None)
    assert base.MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED is False
    assert base.OLLAMA_VERIFIER_BASE_URL is None
    assert base.OLLAMA_VERIFIER_MODELS_URL is None
    assert base.OLLAMA_VERIFIER_MODEL is None
    assert base.OLLAMA_VERIFIER_TIMEOUT_SECONDS is None
    configured = settings(
        independent=True,
        OLLAMA_VERIFIER_BASE_URL="http://verifier/generate",
        OLLAMA_VERIFIER_MODELS_URL="http://verifier/models",
        OLLAMA_VERIFIER_MODEL="verifier-model",
        OLLAMA_VERIFIER_TIMEOUT_SECONDS=30,
    )
    assert configured.OLLAMA_VERIFIER_MODEL == "verifier-model"
    assert configured.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert base.MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED is False


def test_absent_overrides_inherit_custom_primary_values_by_value() -> None:
    configured = settings(
        independent=True,
        OLLAMA_BASE_URL="http://custom-primary/generate",
        OLLAMA_MODELS_URL="http://custom-primary/models",
        OLLAMA_MODEL="custom-primary-model",
        OLLAMA_TIMEOUT_SECONDS=77,
    )
    container = Container(configured)
    verifier = container.claim_verifier_ollama_client
    assert verifier.url == "http://custom-primary/generate"
    assert verifier.models_url == "http://custom-primary/models"
    assert verifier.model == "custom-primary-model"
    assert verifier.timeout_seconds == 77
    assert configured.OLLAMA_VERIFIER_BASE_URL is None
    assert configured.OLLAMA_VERIFIER_MODEL is None


@pytest.mark.parametrize(
    ("override", "value", "client_attribute"),
    (
        ("OLLAMA_VERIFIER_BASE_URL", "http://verifier/generate", "url"),
        ("OLLAMA_VERIFIER_MODELS_URL", "http://verifier/models", "models_url"),
        ("OLLAMA_VERIFIER_MODEL", "verifier-model", "model"),
        ("OLLAMA_VERIFIER_TIMEOUT_SECONDS", 33, "timeout_seconds"),
    ),
)
def test_each_explicit_override_replaces_only_its_corresponding_value(
    override: str,
    value: str | int,
    client_attribute: str,
) -> None:
    configured = settings(
        independent=True,
        OLLAMA_BASE_URL="http://primary/generate",
        OLLAMA_MODELS_URL="http://primary/models",
        OLLAMA_MODEL="primary-model",
        OLLAMA_TIMEOUT_SECONDS=11,
        **{override: value},
    )
    container = Container(configured)
    verifier = container.claim_verifier_ollama_client
    assert getattr(verifier, client_attribute) == value
    assert container.ollama_client.model == "primary-model"
    assert configured.model_dump()[override] == value


@pytest.mark.parametrize("timeout", (0, -1))
def test_verifier_timeout_must_be_positive(timeout: int) -> None:
    with pytest.raises(ValidationError):
        settings(OLLAMA_VERIFIER_TIMEOUT_SECONDS=timeout)


def test_shared_mode_reuses_primary_client_without_secondary_client() -> None:
    container = Container(settings(independent=False))
    assert container.claim_evidence_verifier._client is container.ollama_client
    assert container.claim_verifier_ollama_client is None
    assert container.claim_verifier_readiness_probe is None


def test_independent_mode_uses_separate_configured_client_by_identity() -> None:
    container = Container(
        settings(
            independent=True,
            OLLAMA_BASE_URL="http://primary/generate",
            OLLAMA_MODEL="primary-model",
            OLLAMA_TIMEOUT_SECONDS=10,
            OLLAMA_VERIFIER_BASE_URL="http://verifier/generate",
            OLLAMA_VERIFIER_MODELS_URL="http://verifier/models",
            OLLAMA_VERIFIER_MODEL="verifier-model",
            OLLAMA_VERIFIER_TIMEOUT_SECONDS=20,
        )
    )
    verifier_client = container.claim_verifier_ollama_client
    assert verifier_client is not None
    assert container.ollama_reasoning_provider._client is container.ollama_client
    assert container.claim_evidence_verifier._client is verifier_client
    assert verifier_client is not container.ollama_client
    assert container.ollama_client.url == "http://primary/generate"
    assert container.ollama_client.model == "primary-model"
    assert verifier_client.url == "http://verifier/generate"
    assert verifier_client.model == "verifier-model"
    assert verifier_client.timeout_seconds == 20


def test_flag_matrix_does_not_activate_earlier_modes() -> None:
    historical = Container(settings(grounded=False, independent=True))
    sprint17 = Container(settings(claim=False, independent=True))
    sprint18 = Container(settings(verification=False, independent=True))
    assert historical.reasoning_provider is historical.ollama_reasoning_provider
    assert isinstance(sprint17.reasoning_provider, EvidenceBoundedReasoningProvider)
    assert isinstance(sprint18.reasoning_provider, ClaimEvidenceAttributionProvider)
    for container in (historical, sprint17, sprint18):
        assert container.claim_verifier_ollama_client is None


def test_independent_container_construction_is_inert(monkeypatch) -> None:
    from app.models.ollama_client import OllamaClient
    from app.models.ollama_readiness_probe import OllamaReadinessProbe

    calls = Mock()
    monkeypatch.setattr(OllamaClient, "chat", calls.chat)
    monkeypatch.setattr(OllamaClient, "list_models", calls.list_models)
    monkeypatch.setattr(OllamaReadinessProbe, "check", calls.check)
    Container(settings(independent=True))
    assert calls.mock_calls == []


def test_independent_calls_primary_then_verifier_once_without_third_call() -> None:
    prompt = "What is the codename?"
    scope = MemoryScope("scope")
    container = Container(
        settings(
            independent=True,
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
        ),
        scoped_memory_records=(
            ScopedMemoryRecord(
                scope,
                query_addressable_demo_content(prompt, "Codename ORBIT."),
            ),
        ),
    )
    order = []
    container.ollama_client.chat = Mock(
        side_effect=lambda value: (
            order.append("primary")
            or (
                '{"status":"answered","claims":['
                '{"text":"Codename ORBIT.","used_record_numbers":[1]}]}'
            )
        )
    )
    container.claim_verifier_ollama_client.chat = Mock(
        side_effect=lambda value: (
            order.append("verifier")
            or (
                '{"status":"verified","claims":['
                '{"claim_number":1,"verdict":"supported"}]}'
            )
        )
    )
    outcome = container.cognitive_engine.process(prompt, memory_scope=scope)
    assert outcome.success is True and outcome.response.startswith("Claim 1:")
    assert order == ["primary", "verifier"]
    container.ollama_client.chat.assert_called_once()
    container.claim_verifier_ollama_client.chat.assert_called_once()


def test_independent_verifier_failure_has_no_primary_fallback() -> None:
    import requests

    prompt = "What is the codename?"
    scope = MemoryScope("scope")
    container = Container(
        settings(
            independent=True,
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
        ),
        scoped_memory_records=(
            ScopedMemoryRecord(
                scope,
                query_addressable_demo_content(prompt, "Codename ORBIT."),
            ),
        ),
    )
    container.ollama_client.chat = Mock(
        return_value=(
            '{"status":"answered","claims":['
            '{"text":"Codename ORBIT.","used_record_numbers":[1]}]}'
        )
    )
    container.claim_verifier_ollama_client.chat = Mock(
        side_effect=requests.Timeout("private verifier url")
    )
    outcome = container.cognitive_engine.process(prompt, memory_scope=scope)
    assert outcome.success is False
    assert outcome.error is not None
    assert outcome.error.code == "capability_execution_failed"
    container.ollama_client.chat.assert_called_once()
    container.claim_verifier_ollama_client.chat.assert_called_once()


def test_primary_failure_never_calls_independent_verifier() -> None:
    import requests

    container = Container(settings(independent=True, REASONING_ENABLED=True))
    container.ollama_client.chat = Mock(
        side_effect=requests.ConnectionError("private primary url")
    )
    container.claim_verifier_ollama_client.chat = Mock()
    with pytest.raises(requests.ConnectionError):
        container.cognitive_engine.process("prompt")
    container.ollama_client.chat.assert_called_once()
    container.claim_verifier_ollama_client.chat.assert_not_called()


def test_malformed_independent_verifier_has_no_primary_fallback() -> None:
    prompt = "What is the codename?"
    scope = MemoryScope("scope")
    container = Container(
        settings(
            independent=True,
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
        ),
        scoped_memory_records=(
            ScopedMemoryRecord(
                scope,
                query_addressable_demo_content(prompt, "Codename ORBIT."),
            ),
        ),
    )
    container.ollama_client.chat = Mock(
        return_value=(
            '{"status":"answered","claims":['
            '{"text":"Codename ORBIT.","used_record_numbers":[1]}]}'
        )
    )
    container.claim_verifier_ollama_client.chat = Mock(
        return_value="private malformed verifier output"
    )
    outcome = container.cognitive_engine.process(prompt, memory_scope=scope)
    assert outcome.success is False
    assert outcome.error is not None
    assert outcome.error.code == "claim_evidence_verification_protocol_invalid"
    container.ollama_client.chat.assert_called_once()
    container.claim_verifier_ollama_client.chat.assert_called_once()

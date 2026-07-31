"""Container flag matrix and claim protocol integration."""

from unittest.mock import Mock

from app.cognition.grounding.claim_formatter import ClaimEvidenceFormatter
from app.cognition.grounding.claim_parser import JsonClaimEvidenceResponseParser
from app.cognition.grounding.claim_provider import ClaimEvidenceAttributionProvider
from app.cognition.grounding.parser import JsonGroundedResponseParser
from app.cognition.grounding.provider import EvidenceBoundedReasoningProvider
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.cognition.prompts.reasoning import (
    ClaimEvidenceAttributionPromptBuilder,
    EvidenceBoundedReasoningPromptBuilder,
    MemoryAwareReasoningPromptBuilder,
)
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content


def make(*, grounded: bool, claim: bool) -> Container:
    prompt = "What is Luxiom?"
    scope = MemoryScope("scope")
    return Container(
        Settings(
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
            MEMORY_GROUNDED_RESPONSE_ENABLED=grounded,
            MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED=claim,
            _env_file=None,
        ),
        scoped_memory_records=(
            ScopedMemoryRecord(scope, query_addressable_demo_content(prompt, "record")),
        ),
    )


def test_container_matrix_uses_exactly_one_decorator() -> None:
    historical = make(grounded=False, claim=False)
    ignored_claim = make(grounded=False, claim=True)
    sprint17 = make(grounded=True, claim=False)
    sprint18 = make(grounded=True, claim=True)
    assert historical.reasoning_provider is historical.ollama_reasoning_provider
    assert ignored_claim.reasoning_provider is ignored_claim.ollama_reasoning_provider
    assert isinstance(sprint17.reasoning_provider, EvidenceBoundedReasoningProvider)
    assert isinstance(sprint18.reasoning_provider, ClaimEvidenceAttributionProvider)
    assert isinstance(
        historical.reasoning_prompt_builder, MemoryAwareReasoningPromptBuilder
    )
    assert isinstance(
        ignored_claim.reasoning_prompt_builder, MemoryAwareReasoningPromptBuilder
    )
    assert isinstance(
        sprint17.reasoning_prompt_builder, EvidenceBoundedReasoningPromptBuilder
    )
    assert isinstance(
        sprint18.reasoning_prompt_builder, ClaimEvidenceAttributionPromptBuilder
    )
    assert isinstance(sprint17.grounded_response_parser, JsonGroundedResponseParser)
    assert isinstance(
        sprint18.claim_evidence_response_parser,
        JsonClaimEvidenceResponseParser,
    )
    assert sprint18.grounded_response_parser is None
    assert sprint17.claim_evidence_response_parser is None
    assert historical.claim_evidence_formatter is None
    assert ignored_claim.claim_evidence_formatter is None
    assert sprint17.claim_evidence_formatter is None
    assert isinstance(sprint18.claim_evidence_formatter, ClaimEvidenceFormatter)
    assert sprint17.reasoning_provider._provider is sprint17.ollama_reasoning_provider
    assert sprint18.reasoning_provider._provider is sprint18.ollama_reasoning_provider
    assert (
        sprint17.reasoning_prompt_builder._evidence_selector
        is sprint17.reasoning_provider._evidence_selector
        is sprint17.memory_evidence_selector
    )
    assert (
        sprint18.reasoning_prompt_builder._evidence_selector
        is sprint18.reasoning_provider._selector
        is sprint18.memory_evidence_selector
    )


def test_container_construction_performs_no_runtime_operations(monkeypatch) -> None:
    from app.cognition.engine import CognitiveEngine
    from app.cognition.grounding.claim_parser import JsonClaimEvidenceResponseParser
    from app.cognition.memory.scoped.context_retriever import (
        RepositoryMemoryContextRetriever,
    )
    from app.cognition.memory.scoped.explicit_update import ExplicitMemoryUpdateService
    from app.models.ollama_client import OllamaClient
    from app.models.ollama_readiness_probe import OllamaReadinessProbe

    calls = Mock()
    monkeypatch.setattr(OllamaClient, "chat", calls.chat)
    monkeypatch.setattr(OllamaReadinessProbe, "check", calls.readiness)
    monkeypatch.setattr(RepositoryMemoryContextRetriever, "retrieve", calls.retrieve)
    monkeypatch.setattr(ExplicitMemoryUpdateService, "remember", calls.remember)
    monkeypatch.setattr(JsonClaimEvidenceResponseParser, "parse", calls.parse)
    monkeypatch.setattr(CognitiveEngine, "process", calls.process)

    make(grounded=True, claim=True)

    assert calls.mock_calls == []


def test_claim_json_reaches_auditable_outcome_once() -> None:
    container = make(grounded=True, claim=True)
    container.ollama_client.chat = Mock(
        return_value=(
            '{"status":"answered","claims":[{"text":"fact one",'
            '"used_record_numbers":[1]},{"text":"fact two",'
            '"used_record_numbers":[1]}]}'
        )
    )
    outcome = container.cognitive_engine.process(
        "What is Luxiom?", memory_scope=MemoryScope("scope")
    )
    assert outcome.success and "Claim 2:" in outcome.response
    assert "scope\n" not in outcome.response
    container.ollama_client.chat.assert_called_once()

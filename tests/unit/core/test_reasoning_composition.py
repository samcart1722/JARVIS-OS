"""Tests for reasoning composition without external calls."""

from unittest.mock import Mock

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.domain import Domain
from app.cognition.grounding.parser import JsonGroundedResponseParser
from app.cognition.grounding.provider import (
    EvidenceBoundedReasoningProvider,
)
from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
)
from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)
from app.cognition.planning.goal import Goal
from app.cognition.prompts.reasoning import (
    EvidenceBoundedReasoningPromptBuilder,
    MemoryAwareReasoningPromptBuilder,
)
from app.core.config import Settings
from app.core.container import Container
from app.models.ollama_readiness_probe import OllamaReadinessProbe


def context(prompt: str = "Question") -> CognitiveContext:
    goal = Goal(description=prompt)
    return CognitiveContext(
        raw_input=prompt,
        normalized_input=prompt,
        goal=goal,
    )


def test_container_registers_both_runtime_capabilities() -> None:
    container = Container()

    assert isinstance(
        container.capability_registry.get(NORMALIZED_INPUT_CAPABILITY_ID),
        NormalizedInputCapability,
    )
    assert isinstance(
        container.capability_registry.get(REASONING_CAPABILITY_ID),
        ReasoningCapability,
    )
    assert isinstance(
        container.provider_readiness_probe,
        OllamaReadinessProbe,
    )
    assert isinstance(
        container.scoped_memory_repository,
        InMemoryScopedMemoryRepository,
    )
    assert isinstance(
        container.memory_context_retriever,
        RepositoryMemoryContextRetriever,
    )
    assert isinstance(
        container.explicit_memory_update_service,
        ExplicitMemoryUpdateService,
    )
    assert (
        container.memory_context_retriever._repository
        is container.scoped_memory_repository
    )
    assert (
        container.explicit_memory_update_service._writer
        is container.scoped_memory_repository
    )
    assert container.explicit_memory_update_service.enabled is False
    assert container.scoped_memory_repository._records_by_scope == {}


def test_container_construction_does_not_call_ollama(monkeypatch) -> None:
    post = Mock()
    monkeypatch.setattr("app.models.ollama_client.requests.post", post)

    Container()

    post.assert_not_called()


def test_container_composes_memory_flag_without_search(monkeypatch) -> None:
    search = Mock(side_effect=AssertionError("search must be on demand"))
    monkeypatch.setattr(InMemoryScopedMemoryRepository, "search", search)
    configured = Settings(
        MEMORY_RETRIEVAL_ENABLED=True,
        _env_file=None,
    )

    container = Container(configured)

    assert container.cognitive_engine._memory_retrieval_enabled is True
    assert (
        container.cognitive_engine._memory_context_retriever
        is container.memory_context_retriever
    )
    assert container.scoped_memory_repository._records_by_scope == {}
    search.assert_not_called()


def test_container_composes_enabled_update_without_writing_or_reading(
    monkeypatch,
) -> None:
    add = Mock(side_effect=AssertionError("write must be explicit"))
    search = Mock(side_effect=AssertionError("search must be on demand"))
    monkeypatch.setattr(InMemoryScopedMemoryRepository, "add", add)
    monkeypatch.setattr(InMemoryScopedMemoryRepository, "search", search)

    container = Container(
        Settings(MEMORY_UPDATE_ENABLED=True, _env_file=None)
    )

    assert container.explicit_memory_update_service.enabled is True
    assert (
        container.explicit_memory_update_service._writer
        is container.scoped_memory_repository
    )
    add.assert_not_called()
    search.assert_not_called()


def test_container_injects_memory_prompt_policy_settings() -> None:
    configured = Settings(
        MEMORY_PROMPT_CONTEXT_ENABLED=True,
        MEMORY_PROMPT_MAX_RECORDS=2,
        MEMORY_PROMPT_MAX_CHARACTERS=50,
        _env_file=None,
    )

    container = Container(configured)

    assert isinstance(
        container.reasoning_prompt_builder,
        MemoryAwareReasoningPromptBuilder,
    )
    assert (
        container.reasoning_provider._prompt_builder
        is container.reasoning_prompt_builder
    )
    assert container.reasoning_prompt_builder._memory_context_enabled is True
    assert container.reasoning_prompt_builder._max_records == 2
    assert container.reasoning_prompt_builder._max_characters == 50


def test_container_grounded_false_preserves_historical_composition() -> None:
    container = Container(
        Settings(
            MEMORY_GROUNDED_RESPONSE_ENABLED=False,
            _env_file=None,
        )
    )

    assert isinstance(
        container.reasoning_prompt_builder,
        MemoryAwareReasoningPromptBuilder,
    )
    assert container.reasoning_provider is container.ollama_reasoning_provider
    assert container.grounded_response_parser is None


def test_container_grounded_true_composes_shared_evidence_policy() -> None:
    configured = Settings(
        MEMORY_GROUNDED_RESPONSE_ENABLED=True,
        MEMORY_PROMPT_CONTEXT_ENABLED=False,
        _env_file=None,
    )
    original_values = configured.model_dump()

    container = Container(configured)

    assert isinstance(
        container.reasoning_prompt_builder,
        EvidenceBoundedReasoningPromptBuilder,
    )
    assert isinstance(
        container.reasoning_provider,
        EvidenceBoundedReasoningProvider,
    )
    assert isinstance(
        container.grounded_response_parser,
        JsonGroundedResponseParser,
    )
    assert (
        container.reasoning_prompt_builder._evidence_selector
        is container.memory_evidence_selector
    )
    assert (
        container.reasoning_provider._evidence_selector
        is container.memory_evidence_selector
    )
    scope = MemoryScope("scope")
    context = CognitiveContext(
        raw_input="request",
        normalized_input="request",
        memory_snapshot=MemorySnapshot(
            scope=scope,
            records=(ScopedMemoryRecord(scope, "evidence"),),
        ),
    )
    prompt = container.reasoning_prompt_builder.build(context)

    assert "[EVIDENCE-BOUNDED RESPONSE PROTOCOL]" in prompt
    assert configured.MEMORY_PROMPT_CONTEXT_ENABLED is False
    assert configured.MEMORY_GROUNDED_RESPONSE_ENABLED is True
    assert configured.model_dump() == original_values


def test_container_accepts_explicit_ephemeral_scoped_records() -> None:
    scope = MemoryScope("demo-scope")
    record = ScopedMemoryRecord(scope, "Prompt reference")

    container = Container(
        Settings(_env_file=None),
        scoped_memory_records=(record,),
    )

    assert container.scoped_memory_repository.search(
        scope, "Prompt"
    ) == (record,)


def test_container_defensively_copies_mutable_scoped_record_collection() -> None:
    scope = MemoryScope("scope-a")
    record = ScopedMemoryRecord(scope, "Prompt reference")
    records = [record]

    container = Container(
        Settings(_env_file=None),
        scoped_memory_records=records,
    )
    records.clear()

    assert container._scoped_memory_records == (record,)
    assert container.scoped_memory_repository.search(
        scope, "Prompt"
    ) == (record,)


def test_container_rejects_text_as_scoped_record_collection() -> None:
    import pytest

    with pytest.raises(TypeError, match="collection of records"):
        Container(
            Settings(_env_file=None),
            scoped_memory_records="not records",
        )


def test_container_preserves_scope_isolation_for_injected_records() -> None:
    scope_a = MemoryScope("scope-a")
    scope_b = MemoryScope("scope-b")
    record_a = ScopedMemoryRecord(scope_a, "Shared prompt A")
    record_b = ScopedMemoryRecord(scope_b, "Shared prompt B")

    container = Container(
        Settings(_env_file=None),
        scoped_memory_records=[record_a, record_b],
    )

    assert container.scoped_memory_repository.search(
        scope_a, "Shared prompt"
    ) == (record_a,)
    assert container.scoped_memory_repository.search(
        scope_b, "Shared prompt"
    ) == (record_b,)


def test_default_specialist_keeps_deterministic_capability_policy() -> None:
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None)
    )
    specialist = container.specialist_router.route(Domain.UNKNOWN)
    plan = specialist.create_plan(context())

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == NORMALIZED_INPUT_CAPABILITY_ID


def test_container_injects_official_settings_into_ollama_client() -> None:
    configured = Settings(
        OLLAMA_BASE_URL="http://configured.test/api/generate",
        OLLAMA_MODELS_URL="http://configured.test/api/tags",
        OLLAMA_MODEL="configured-model",
        OLLAMA_TIMEOUT_SECONDS=30,
        _env_file=None,
    )

    container = Container(configured)

    assert container.ollama_client.url == (
        "http://configured.test/api/generate"
    )
    assert container.ollama_client.model == "configured-model"
    assert container.ollama_client.models_url == "http://configured.test/api/tags"
    assert container.ollama_client.timeout_seconds == 30


def test_container_composes_reasoning_selection_from_settings() -> None:
    disabled = Container(
        Settings(REASONING_ENABLED=False, _env_file=None)
    )
    enabled = Container(Settings(REASONING_ENABLED=True, _env_file=None))

    assert disabled.reasoning_selection_policy.reasoning_enabled is False
    assert enabled.reasoning_selection_policy.reasoning_enabled is True
    assert (
        disabled.default_specialist.create_plan(context()).steps[0].capability_id
        == NORMALIZED_INPUT_CAPABILITY_ID
    )
    assert (
        enabled.default_specialist.create_plan(context()).steps[0].capability_id
        == REASONING_CAPABILITY_ID
    )


def test_enabled_reasoning_reaches_real_provider_output_without_network() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(return_value="Controlled reasoning")

    response = container.cognitive_engine.process("Any prompt")

    assert response.success is True
    assert response.response == "Controlled reasoning"
    assert response.error is None
    container.ollama_client.chat.assert_called_once_with("Any prompt")


def test_enabled_reasoning_failure_has_no_normalized_input_fallback() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(return_value="")

    response = container.cognitive_engine.process("Must not be fallback")

    assert response.success is False
    assert response.response is None
    assert response.error is not None
    assert response.error.code == "empty_capability_output"


def test_enabled_reasoning_exception_propagates_without_fallback() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(
        side_effect=RuntimeError("controlled provider error")
    )

    import pytest

    with pytest.raises(RuntimeError, match="controlled provider error"):
        container.cognitive_engine.process("Must not be fallback")

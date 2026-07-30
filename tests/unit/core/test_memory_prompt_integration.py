"""Controlled integration tests for scoped memory-aware reasoning prompts."""

from unittest.mock import Mock

from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container


def configured_container(
    *,
    prompt_context_enabled: bool,
    records: tuple[ScopedMemoryRecord, ...],
) -> Container:
    container = Container(
        Settings(
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=prompt_context_enabled,
            MEMORY_PROMPT_MAX_RECORDS=5,
            MEMORY_PROMPT_MAX_CHARACTERS=2000,
            _env_file=None,
        )
    )
    repository = InMemoryScopedMemoryRepository(records)
    container.cognitive_engine._memory_context_retriever = (
        RepositoryMemoryContextRetriever(repository)
    )
    container.ollama_client.chat = Mock(return_value="Reasoned output")
    return container


def test_enabled_retrieval_and_prompt_context_build_structured_prompt() -> None:
    scope = MemoryScope("scope-a")
    container = configured_container(
        prompt_context_enabled=True,
        records=(ScopedMemoryRecord(scope, "Current request owned reference"),),
    )

    outcome = container.cognitive_engine.process(
        "Current request",
        memory_scope=scope,
    )

    assert outcome.success is True
    prompt = container.ollama_client.chat.call_args.args[0]
    assert prompt.startswith("[CURRENT USER REQUEST]\nCurrent request")
    assert '"Current request owned reference"' in prompt
    assert scope.identifier not in prompt


def test_retrieval_with_prompt_context_disabled_uses_historical_prompt() -> None:
    scope = MemoryScope("scope-a")
    container = configured_container(
        prompt_context_enabled=False,
        records=(ScopedMemoryRecord(scope, "Current request owned reference"),),
    )

    container.cognitive_engine.process("Current request", memory_scope=scope)

    container.ollama_client.chat.assert_called_once_with("Current request")


def test_prompt_context_enabled_without_scope_uses_historical_prompt() -> None:
    container = configured_container(
        prompt_context_enabled=True,
        records=(),
    )

    container.cognitive_engine.process("Current request")

    container.ollama_client.chat.assert_called_once_with("Current request")


def test_empty_snapshot_uses_historical_prompt() -> None:
    scope = MemoryScope("scope-a")
    container = configured_container(
        prompt_context_enabled=True,
        records=(),
    )

    container.cognitive_engine.process("Current request", memory_scope=scope)

    container.ollama_client.chat.assert_called_once_with("Current request")


def test_memory_from_another_scope_is_not_used() -> None:
    requested = MemoryScope("scope-a")
    other = MemoryScope("scope-b")
    container = configured_container(
        prompt_context_enabled=True,
        records=(ScopedMemoryRecord(other, "Other private reference"),),
    )

    container.cognitive_engine.process(
        "Current request",
        memory_scope=requested,
    )

    container.ollama_client.chat.assert_called_once_with("Current request")

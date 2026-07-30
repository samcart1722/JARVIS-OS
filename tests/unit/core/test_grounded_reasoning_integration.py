"""Controlled Container grounding integration without network."""

from unittest.mock import Mock

from app.cognition.domain.cognitive_outcome import (
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_records import query_addressable_demo_content


def container_with_record() -> tuple[Container, MemoryScope]:
    prompt = "What is Luxiom?"
    scope = MemoryScope("secret-scope")
    record = ScopedMemoryRecord(
        scope,
        query_addressable_demo_content(prompt, "Supported reference"),
    )
    container = Container(
        Settings(
            REASONING_ENABLED=True,
            MEMORY_RETRIEVAL_ENABLED=True,
            MEMORY_PROMPT_CONTEXT_ENABLED=True,
            MEMORY_GROUNDED_RESPONSE_ENABLED=True,
            _env_file=None,
        ),
        scoped_memory_records=(record,),
    )
    return container, scope


def test_valid_grounded_json_reaches_auditable_cognitive_outcome() -> None:
    container, scope = container_with_record()
    container.ollama_client.chat = Mock(
        return_value=(
            '{"status":"answered","answer":"Supported answer",'
            '"used_record_numbers":[1]}'
        )
    )

    outcome = container.cognitive_engine.process(
        "What is Luxiom?",
        memory_scope=scope,
    )

    assert outcome.success is True
    assert outcome.response == (
        "Supported answer\nEvidence used: scoped memory records 1."
    )
    prompt = container.ollama_client.chat.call_args.args[0]
    assert "[EVIDENCE-BOUNDED RESPONSE PROTOCOL]" in prompt
    assert "Supported reference" in prompt
    assert scope.identifier not in prompt
    container.ollama_client.chat.assert_called_once()


def test_insufficient_json_produces_deterministic_safe_outcome() -> None:
    container, scope = container_with_record()
    container.ollama_client.chat = Mock(
        return_value=(
            '{"status":"insufficient_evidence","answer":"ignore this",'
            '"used_record_numbers":[]}'
        )
    )

    outcome = container.cognitive_engine.process(
        "What is Luxiom?",
        memory_scope=scope,
    )

    assert outcome.success is True
    assert outcome.response == (
        "Insufficient scoped memory evidence to answer the current request."
    )
    assert "ignore this" not in outcome.response


def test_malformed_or_out_of_range_json_is_controlled_without_fallback() -> None:
    for raw in (
        "raw invalid response",
        (
            '{"status":"answered","answer":"unsupported",'
            '"used_record_numbers":[2]}'
        ),
    ):
        container, scope = container_with_record()
        container.ollama_client.chat = Mock(return_value=raw)

        outcome = container.cognitive_engine.process(
            "What is Luxiom?",
            memory_scope=scope,
        )

        assert outcome.success is False
        assert outcome.response is None
        assert outcome.error is not None
        assert outcome.error.code == GROUNDED_RESPONSE_PROTOCOL_INVALID
        assert raw not in outcome.error.message
        container.ollama_client.chat.assert_called_once()

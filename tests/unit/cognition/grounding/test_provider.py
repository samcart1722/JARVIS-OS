"""Tests for the evidence-bounded reasoning provider decorator."""

from unittest.mock import Mock

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import (
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.parser import GroundedResponseParser
from app.cognition.grounding.provider import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    EvidenceBoundedReasoningProvider,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)
from app.cognition.providers.base_provider import ReasoningProvider


def context(with_records: bool) -> CognitiveContext:
    scope = MemoryScope("secret-scope")
    snapshot = (
        MemorySnapshot(
            scope,
            (ScopedMemoryRecord(scope, "evidence"),),
        )
        if with_records
        else None
    )
    return CognitiveContext(
        raw_input="request",
        normalized_input="request",
        memory_snapshot=snapshot,
    )


def decorator(
    inner: Mock,
    parser: Mock,
    *,
    enabled: bool = True,
) -> EvidenceBoundedReasoningProvider:
    return EvidenceBoundedReasoningProvider(
        inner,
        parser,
        MemoryEvidenceSelector(max_records=2, max_characters=100),
        enabled=enabled,
    )


def test_disabled_none_and_empty_snapshot_are_exact_pass_through() -> None:
    result = ReasoningResult(response="  unchanged  ")
    for enabled, ctx in (
        (False, context(True)),
        (True, context(False)),
        (
            True,
            CognitiveContext(
                raw_input="request",
                normalized_input="request",
                memory_snapshot=MemorySnapshot(
                    MemoryScope("secret-scope"),
                    (),
                ),
            ),
        ),
    ):
        inner = Mock(spec=ReasoningProvider)
        inner.generate.return_value = result
        parser = Mock(spec=GroundedResponseParser)

        actual = decorator(inner, parser, enabled=enabled).generate(ctx)

        assert actual is result
        inner.generate.assert_called_once_with(ctx)
        parser.parse.assert_not_called()


def test_answered_response_adds_stable_evidence_footer() -> None:
    inner = Mock(spec=ReasoningProvider)
    inner.generate.return_value = ReasoningResult(
        response=(
            '{"status":"answered","answer":"Supported answer",'
            '"used_record_numbers":[1]}'
        )
    )
    from app.cognition.grounding.parser import JsonGroundedResponseParser

    result = decorator(
        inner,
        Mock(wraps=JsonGroundedResponseParser()),
    ).generate(context(True))

    assert result == ReasoningResult(
        response=(
            "Supported answer\nEvidence used: scoped memory records 1."
        )
    )
    inner.generate.assert_called_once()
    assert "secret-scope" not in result.response


def test_insufficient_evidence_ignores_free_model_wording() -> None:
    inner = Mock(spec=ReasoningProvider)
    inner.generate.return_value = ReasoningResult(
        response=(
            '{"status":"insufficient_evidence",'
            '"answer":"untrusted free wording","used_record_numbers":[]}'
        )
    )
    from app.cognition.grounding.parser import JsonGroundedResponseParser

    result = decorator(
        inner,
        Mock(wraps=JsonGroundedResponseParser()),
    ).generate(context(True))

    assert result == ReasoningResult(response=INSUFFICIENT_EVIDENCE_MESSAGE)
    assert "untrusted free wording" not in result.response


def test_invalid_protocol_returns_controlled_failure_without_fallback() -> None:
    raw = "not valid JSON secret raw response"
    inner = Mock(spec=ReasoningProvider)
    inner.generate.return_value = ReasoningResult(response=raw)
    from app.cognition.grounding.parser import JsonGroundedResponseParser

    result = decorator(
        inner,
        Mock(wraps=JsonGroundedResponseParser()),
    ).generate(context(True))

    assert result == ReasoningResult(
        response="",
        error_code=GROUNDED_RESPONSE_PROTOCOL_INVALID,
    )
    assert raw not in result.response
    inner.generate.assert_called_once()


def test_inner_controlled_failure_is_preserved_without_parsing() -> None:
    failure = ReasoningResult(response="", error_code="inner_failure")
    inner = Mock(spec=ReasoningProvider)
    inner.generate.return_value = failure
    parser = Mock(spec=GroundedResponseParser)

    result = decorator(inner, parser).generate(context(True))

    assert result is failure
    inner.generate.assert_called_once()
    parser.parse.assert_not_called()

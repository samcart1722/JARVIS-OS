"""Strict parsing of untrusted closed provider JSON; no repairs or coercion."""

import json

from app.cognition.intent_preparation.models import (
    MAX_PROVIDER_RESPONSE_BYTES,
    Candidate,
    Intent,
    ProviderOutcome,
    has_isolated_surrogate,
)


class CandidateParseError(ValueError):
    """Sanitized closed-output rejection; never exposes provider text."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key.")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError("Non-JSON number.")


def parse_candidate(provider_text: object) -> Candidate:
    """Parse exactly one bounded object; model output remains semantic data."""
    if type(provider_text) is not str:
        raise CandidateParseError("Invalid provider output.")
    if len(provider_text) > MAX_PROVIDER_RESPONSE_BYTES:
        raise CandidateParseError("Provider output exceeds the response limit.")
    if has_isolated_surrogate(provider_text):
        raise CandidateParseError("Invalid provider output.")
    # UTF-8 requires at least one byte per code point; the length cap runs first.
    if len(provider_text.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
        raise CandidateParseError("Provider output exceeds the response limit.")
    try:
        payload = json.loads(
            provider_text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if type(payload) is not dict or set(payload) != {"outcome", "intent", "fields"}:
            raise ValueError("Invalid top-level shape.")
        if type(payload["outcome"]) is not str or type(payload["fields"]) is not dict:
            raise ValueError("Invalid outcome or fields.")
        outcome = ProviderOutcome(payload["outcome"])
        if outcome is ProviderOutcome.UNSUPPORTED:
            if payload["intent"] is not None or payload["fields"]:
                raise ValueError("Unsupported output contains semantic data.")
            return Candidate(outcome, None)
        if type(payload["intent"]) is not str:
            raise ValueError("Invalid intent.")
        return Candidate(
            outcome, Intent(payload["intent"]), tuple(payload["fields"].items())
        )
    except (ValueError, TypeError, RecursionError):
        raise CandidateParseError("Invalid closed provider candidate.") from None

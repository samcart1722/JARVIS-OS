"""Strict standard-library parser for grounded JSON responses."""

import json
from typing import Protocol

from app.cognition.grounding.models import GroundedResponseEnvelope

_EXPECTED_FIELDS = frozenset(
    ("status", "answer", "used_record_numbers")
)
_SAFE_PROTOCOL_MESSAGE = (
    "The reasoning provider returned an invalid evidence-bounded response."
)


class GroundedResponseProtocolError(ValueError):
    """Represent a safe protocol failure without retaining raw model output."""

    def __init__(self) -> None:
        super().__init__(_SAFE_PROTOCOL_MESSAGE)


class GroundedResponseParser(Protocol):
    """Decode and validate one evidence-bounded provider response."""

    def parse(
        self,
        raw_response: str,
        *,
        max_record_number: int,
    ) -> GroundedResponseEnvelope:
        """Return a strict validated envelope or raise a safe error."""


class JsonGroundedResponseParser:
    """Reject any response outside the exact JSON envelope."""

    def parse(
        self,
        raw_response: str,
        *,
        max_record_number: int,
    ) -> GroundedResponseEnvelope:
        """Parse one complete JSON object without repair or extraction."""
        try:
            payload = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            payload = None
        if (
            not isinstance(raw_response, str)
            or not raw_response.strip()
            or max_record_number <= 0
            or type(payload) is not dict
            or frozenset(payload) != _EXPECTED_FIELDS
        ):
            raise GroundedResponseProtocolError
        status = payload["status"]
        answer = payload["answer"]
        references = payload["used_record_numbers"]
        if (
            type(status) is not str
            or type(answer) is not str
            or type(references) is not list
            or any(type(number) is not int for number in references)
        ):
            raise GroundedResponseProtocolError
        try:
            envelope = GroundedResponseEnvelope(
                status=status,
                answer=answer,
                used_record_numbers=tuple(references),
            )
        except (TypeError, ValueError):
            raise GroundedResponseProtocolError from None
        if any(
            number > max_record_number
            for number in envelope.used_record_numbers
        ):
            raise GroundedResponseProtocolError
        return envelope

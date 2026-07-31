"""Strict JSON parser for claim-level evidence attribution."""

import json
from typing import Protocol

from app.cognition.grounding.claim_models import (
    ClaimEvidence,
    ClaimGroundedResponseEnvelope,
)
from app.cognition.grounding.parser import GroundedResponseProtocolError


class ClaimEvidenceResponseParser(Protocol):
    def parse(
        self,
        raw_response: str,
        *,
        max_record_number: int,
    ) -> ClaimGroundedResponseEnvelope:
        """Return a strict envelope or raise a safe protocol error."""


class JsonClaimEvidenceResponseParser:
    """Parse exactly one complete claim-level JSON object."""

    def parse(
        self,
        raw_response: str,
        *,
        max_record_number: int,
    ) -> ClaimGroundedResponseEnvelope:
        if (
            not isinstance(raw_response, str)
            or not raw_response.strip()
            or type(max_record_number) is not int
            or max_record_number <= 0
        ):
            raise GroundedResponseProtocolError
        try:
            payload = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            raise GroundedResponseProtocolError from None
        if type(payload) is not dict or set(payload) != {"status", "claims"}:
            raise GroundedResponseProtocolError
        if type(payload["status"]) is not str or type(payload["claims"]) is not list:
            raise GroundedResponseProtocolError
        claims: list[ClaimEvidence] = []
        try:
            for item in payload["claims"]:
                if type(item) is not dict or set(item) != {
                    "text",
                    "used_record_numbers",
                }:
                    raise GroundedResponseProtocolError
                if (
                    type(item["text"]) is not str
                    or type(item["used_record_numbers"]) is not list
                ):
                    raise GroundedResponseProtocolError
                references = item["used_record_numbers"]
                if any(type(number) is not int for number in references):
                    raise GroundedResponseProtocolError
                claim = ClaimEvidence(item["text"], tuple(references))
                if any(
                    number > max_record_number for number in claim.used_record_numbers
                ):
                    raise GroundedResponseProtocolError
                claims.append(claim)
            return ClaimGroundedResponseEnvelope(payload["status"], tuple(claims))
        except (TypeError, ValueError):
            raise GroundedResponseProtocolError from None

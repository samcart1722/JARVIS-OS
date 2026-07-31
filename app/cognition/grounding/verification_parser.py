"""Strict parser for claim evidence support verdicts."""

import json
from typing import Protocol

from app.cognition.grounding.verification_models import (
    ClaimEvidenceVerificationEnvelope,
    ClaimSupportVerdict,
)

_SAFE_MESSAGE = "The claim evidence verifier returned an invalid response."


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


class ClaimEvidenceVerificationProtocolError(ValueError):
    def __init__(self) -> None:
        super().__init__(_SAFE_MESSAGE)


class ClaimEvidenceVerificationParser(Protocol):
    def parse(
        self, raw_response: str, *, claim_count: int
    ) -> ClaimEvidenceVerificationEnvelope: ...


class JsonClaimEvidenceVerificationParser:
    def parse(
        self, raw_response: str, *, claim_count: int
    ) -> ClaimEvidenceVerificationEnvelope:
        if (
            not isinstance(raw_response, str)
            or not raw_response.strip()
            or type(claim_count) is not int
            or claim_count <= 0
        ):
            raise ClaimEvidenceVerificationProtocolError
        try:
            payload = json.loads(raw_response, object_pairs_hook=_unique_object)
        except (json.JSONDecodeError, TypeError, ValueError):
            raise ClaimEvidenceVerificationProtocolError from None
        if type(payload) is not dict or set(payload) != {"status", "claims"}:
            raise ClaimEvidenceVerificationProtocolError
        if payload["status"] != "verified" or type(payload["claims"]) is not list:
            raise ClaimEvidenceVerificationProtocolError
        try:
            verdicts = []
            for item in payload["claims"]:
                if type(item) is not dict or set(item) != {"claim_number", "verdict"}:
                    raise ClaimEvidenceVerificationProtocolError
                if (
                    type(item["claim_number"]) is not int
                    or type(item["verdict"]) is not str
                ):
                    raise ClaimEvidenceVerificationProtocolError
                verdicts.append(
                    ClaimSupportVerdict(item["claim_number"], item["verdict"])
                )
            envelope = ClaimEvidenceVerificationEnvelope("verified", tuple(verdicts))
        except (TypeError, ValueError):
            raise ClaimEvidenceVerificationProtocolError from None
        if {item.claim_number for item in envelope.claims} != set(
            range(1, claim_count + 1)
        ):
            raise ClaimEvidenceVerificationProtocolError
        return envelope

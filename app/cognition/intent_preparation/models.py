"""Closed immutable semantic data and shared frozen text limits."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

MAX_INPUT_CODE_POINTS = 8192
MAX_PROVIDER_RESPONSE_BYTES = 32768
EDGE_WHITESPACE = (
    "\u0009\u000a\u000b\u000c\u000d\u001c\u001d\u001e\u001f\u0020"
    "\u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
)


def strip_edge_whitespace(value: str) -> str:
    """Trim only the contract's explicit whitespace set; preserve interior text."""
    return value.strip(EDGE_WHITESPACE)


def has_isolated_surrogate(value: str) -> bool:
    """Python strings contain code points; surrogate code points are invalid."""
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def is_bounded_input(value: object) -> bool:
    return (
        type(value) is str
        and 0 < len(value) <= MAX_INPUT_CODE_POINTS
        and not has_isolated_surrogate(value)
        and bool(strip_edge_whitespace(value))
    )


class Intent(str, Enum):
    CAPTURE_KNOWLEDGE = "CAPTURE_KNOWLEDGE"
    RECALL_KNOWLEDGE = "RECALL_KNOWLEDGE"
    ADD_FOLLOW_UP = "ADD_FOLLOW_UP"
    READ_FOLLOW_UP = "READ_FOLLOW_UP"


class ProviderOutcome(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


FIELD_ORDER = MappingProxyType(
    {
        Intent.CAPTURE_KNOWLEDGE: ("value",),
        Intent.RECALL_KNOWLEDGE: ("key",),
        Intent.ADD_FOLLOW_UP: ("item", "list_id"),
        Intent.READ_FOLLOW_UP: ("list_id",),
    }
)


@dataclass(frozen=True, slots=True)
class Candidate:
    """Schema-checked semantic data; not grounded, eligible or authorized yet."""

    outcome: ProviderOutcome
    intent: Intent | None
    fields: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.outcome) is not ProviderOutcome or type(self.fields) is not tuple:
            raise ValueError("Invalid candidate shape.")
        if self.outcome is ProviderOutcome.UNSUPPORTED:
            if self.intent is not None or self.fields:
                raise ValueError("Unsupported candidate must have no semantic data.")
            return
        if type(self.intent) is not Intent:
            raise ValueError("Supported candidate requires one closed intent.")
        values: dict[str, str] = {}
        for pair in self.fields:
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError("Fields must be immutable name/value pairs.")
            name, value = pair
            if (
                type(name) is not str
                or name not in FIELD_ORDER[self.intent]
                or name in values
                or not is_bounded_input(value)
            ):
                raise ValueError("Invalid semantic field.")
            values[name] = strip_edge_whitespace(value)
        object.__setattr__(
            self,
            "fields",
            tuple(
                (name, values[name])
                for name in FIELD_ORDER[self.intent]
                if name in values
            ),
        )


class EligibilityDecision(str, Enum):
    ELIGIBLE_UNRECOGNIZED = "eligible_unrecognized"
    PROTECTED = "protected"


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    decision: EligibilityDecision
    reason: str

    def __post_init__(self) -> None:
        if (
            type(self.decision) is not EligibilityDecision
            or type(self.reason) is not str
        ):
            raise ValueError("Invalid eligibility result.")
        if not self.reason:
            raise ValueError("Eligibility requires an explicit reason.")


class ValidationStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Semantic completeness only; Capture metadata is still a later user input."""

    status: ValidationStatus
    candidate: Candidate | None = None
    missing_fields: tuple[str, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not ValidationStatus:
            raise ValueError("Invalid validation status.")
        if type(self.missing_fields) is not tuple:
            raise ValueError("Missing fields must be immutable.")
        if self.status is ValidationStatus.REJECTED:
            if (
                self.candidate is not None
                or self.missing_fields
                or type(self.reason) is not str
                or not self.reason
            ):
                raise ValueError("Rejected result requires only a safe reason.")
            return
        if (
            type(self.candidate) is not Candidate
            or self.candidate.outcome is not ProviderOutcome.SUPPORTED
            or self.reason is not None
        ):
            raise ValueError("Accepted validation requires supported semantic data.")
        present = dict(self.candidate.fields)
        missing = tuple(
            name for name in FIELD_ORDER[self.candidate.intent] if name not in present
        )
        if self.missing_fields != missing:
            raise ValueError("Missing fields must match deterministic semantic order.")
        expected = ValidationStatus.PARTIAL if missing else ValidationStatus.COMPLETE
        if self.status is not expected:
            raise ValueError("Validation status does not match semantic completeness.")

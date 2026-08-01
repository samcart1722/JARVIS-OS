"""Immutable requests and outcomes for explicit local-first coordination."""

from dataclasses import dataclass
from enum import Enum

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.local_resolution.models import (
    KnowledgeResolutionResult,
    LocalResolutionResult,
)

LocalResult = LocalResolutionResult | KnowledgeResolutionResult


class CoordinatedRoute(str, Enum):
    LOCAL = "local"
    COGNITIVE = "cognitive"
    SAFE_INSUFFICIENCY = "safe_insufficiency"


class SafeInsufficiencyReason(str, Enum):
    FALLBACK_NOT_AUTHORIZED = "fallback_not_authorized"
    COGNITIVE_INPUT_INVALID = "cognitive_input_invalid"


@dataclass(frozen=True, slots=True)
class CognitiveFallbackAuthorization:
    allowed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ValueError("Fallback authorization must be an explicit boolean.")


@dataclass(frozen=True, slots=True)
class CoordinatedRequest:
    actor: object
    workspace: object
    local_intent: object
    fallback_authorization: CognitiveFallbackAuthorization
    cognitive_input: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.fallback_authorization, CognitiveFallbackAuthorization
        ):
            raise ValueError("Explicit fallback authorization is required.")


@dataclass(frozen=True, slots=True)
class CoordinatedResult:
    route: CoordinatedRoute
    local_result: LocalResult | None = None
    cognitive_outcome: CognitiveOutcome | None = None
    insufficiency_reason: SafeInsufficiencyReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.route, CoordinatedRoute):
            raise ValueError("Coordinated route is invalid.")
        if self.route is CoordinatedRoute.LOCAL:
            if (
                not isinstance(
                    self.local_result,
                    (LocalResolutionResult, KnowledgeResolutionResult),
                )
                or not self.local_result.handled
                or self.cognitive_outcome is not None
                or self.insufficiency_reason is not None
            ):
                raise ValueError("Local route payload is inconsistent.")
            return
        if self.route is CoordinatedRoute.COGNITIVE:
            if (
                self.cognitive_outcome is None
                or not isinstance(self.cognitive_outcome, CognitiveOutcome)
                or self.local_result is not None
                or self.insufficiency_reason is not None
            ):
                raise ValueError("Cognitive route payload is inconsistent.")
            return
        if (
            not isinstance(self.insufficiency_reason, SafeInsufficiencyReason)
            or self.local_result is not None
            or self.cognitive_outcome is not None
        ):
            raise ValueError("Safe-insufficiency payload is inconsistent.")

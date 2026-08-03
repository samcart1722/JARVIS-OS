"""Application service joining text interpretation to existing coordination."""

from dataclasses import dataclass

from app.cognition.interpretation.contracts import LocalCommandInterpreter
from app.cognition.interpretation.models import (
    UNRECOGNIZED_LOCAL_INTENT,
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
)
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRequest,
    CoordinatedResult,
)


@dataclass(frozen=True, slots=True)
class TextRoutingRequest:
    actor: object
    workspace: object
    text: object
    fallback_authorization: CognitiveFallbackAuthorization

    def __post_init__(self) -> None:
        if not isinstance(self.fallback_authorization, CognitiveFallbackAuthorization):
            raise ValueError("Explicit fallback authorization is required.")


@dataclass(frozen=True, slots=True)
class TextRoutingResult:
    interpretation: LocalCommandInterpretation
    coordinated_result: CoordinatedResult | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation, LocalCommandInterpretation):
            raise ValueError("A valid interpretation result is required.")
        if self.interpretation.status is LocalCommandInterpretationStatus.INVALID:
            if self.coordinated_result is not None:
                raise ValueError("An invalid interpretation cannot be coordinated.")
            return
        if not isinstance(self.coordinated_result, CoordinatedResult):
            raise ValueError(
                "A non-invalid interpretation requires a coordinated result."
            )


class LocalCommandTextRouter:
    def __init__(
        self,
        interpreter: LocalCommandInterpreter,
        coordinator: LocalFirstCognitiveCoordinator,
    ) -> None:
        self._interpreter = interpreter
        self._coordinator = coordinator

    def route(self, request: TextRoutingRequest) -> TextRoutingResult:
        if not isinstance(request, TextRoutingRequest):
            raise TypeError("A valid text-routing request is required.")
        interpretation = self._interpreter.interpret(request.text)
        if interpretation.status is LocalCommandInterpretationStatus.INVALID:
            return TextRoutingResult(interpretation)
        intent = (
            interpretation.intent
            if interpretation.status is LocalCommandInterpretationStatus.INTERPRETED
            else UNRECOGNIZED_LOCAL_INTENT
        )
        coordinated = self._coordinator.coordinate(
            CoordinatedRequest(
                request.actor,
                request.workspace,
                intent,
                request.fallback_authorization,
                request.text,
            )
        )
        return TextRoutingResult(interpretation, coordinated)

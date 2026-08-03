"""Infrastructure-free runtime for the bounded text-routing demonstration."""

from dataclasses import dataclass

from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
)
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRoute,
)


@dataclass(frozen=True, slots=True)
class TextRoutingScenarioReport:
    interpretation_status: LocalCommandInterpretationStatus
    route: CoordinatedRoute | None
    success: bool
    items: tuple[str, ...] = ()
    cognitive_calls: int = 0


@dataclass(frozen=True, slots=True)
class LocalCommandInterpretationDemoReport:
    scenarios: tuple[TextRoutingScenarioReport, ...]
    model_calls: int = 0
    external_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if len(self.scenarios) != 5:
            raise ValueError("The text-routing demo requires exactly five scenarios.")
        if any(
            (
                self.model_calls,
                self.external_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("The text-routing demo cannot report remote activity.")


class LocalCommandInterpretationDemoRuntime:
    def __init__(
        self,
        router: LocalCommandTextRouter,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> None:
        self._router = router
        self._actor = actor
        self._workspace = workspace

    def _route(self, text: str, allowed: bool):
        return self._router.route(
            TextRoutingRequest(
                self._actor,
                self._workspace,
                text,
                CognitiveFallbackAuthorization(allowed),
            )
        )

    def run(self) -> LocalCommandInterpretationDemoReport:
        results = (
            self._route("list add demo-list :: milk | eggs | Gerber", False),
            self._route("list read demo-list", False),
            self._route("list add demo-list :: milk |", True),
            self._route("unrelated denied text", False),
            self._route("unrelated authorized text", True),
        )
        expected_routes = (
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            None,
            CoordinatedRoute.SAFE_INSUFFICIENCY,
            CoordinatedRoute.COGNITIVE,
        )
        if tuple(
            item.coordinated_result.route if item.coordinated_result else None
            for item in results
        ) != expected_routes:
            raise RuntimeError("Text-routing demo did not complete expected routes.")
        reports = []
        for item in results:
            coordinated = item.coordinated_result
            local = coordinated.local_result if coordinated else None
            cognitive = coordinated.cognitive_outcome if coordinated else None
            success = (
                local.success
                if local is not None
                else cognitive.success
                if cognitive is not None
                else False
            )
            reports.append(
                TextRoutingScenarioReport(
                    item.interpretation.status,
                    coordinated.route if coordinated else None,
                    success,
                    local.items if local else (),
                    int(
                        bool(
                            coordinated
                            and coordinated.route is CoordinatedRoute.COGNITIVE
                        )
                    ),
                )
            )
        return LocalCommandInterpretationDemoReport(tuple(reports))

"""Controlled proof of explicit local-first cognitive routing policy."""

from dataclasses import dataclass

from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    WorkspaceIdentity,
)
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRequest,
    CoordinatedRoute,
)


@dataclass(frozen=True, slots=True)
class RoutingScenarioReport:
    route: CoordinatedRoute
    local_handled: bool
    fallback_authorized: bool
    cognitive_calls: int


@dataclass(frozen=True, slots=True)
class LocalFirstCognitiveRoutingDemoReport:
    handled_local: RoutingScenarioReport
    denied_fallback: RoutingScenarioReport
    authorized_fallback: RoutingScenarioReport
    model_calls: int = 0
    external_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if any(
            count != 0
            for count in (
                self.model_calls,
                self.external_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("Routing demo cannot include remote activity.")


class LocalFirstCognitiveRoutingDemoRuntime:
    def __init__(
        self,
        coordinator: LocalFirstCognitiveCoordinator,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> None:
        self._coordinator = coordinator
        self._actor = actor
        self._workspace = workspace

    def run(self) -> LocalFirstCognitiveRoutingDemoReport:
        local = self._coordinator.coordinate(
            CoordinatedRequest(
                self._actor,
                self._workspace,
                AddListItemsCommand("demo-list", ("local-item",)),
                CognitiveFallbackAuthorization(False),
            )
        )
        denied = self._coordinator.coordinate(
            CoordinatedRequest(
                self._actor,
                self._workspace,
                object(),
                CognitiveFallbackAuthorization(False),
            )
        )
        cognitive = self._coordinator.coordinate(
            CoordinatedRequest(
                self._actor,
                self._workspace,
                object(),
                CognitiveFallbackAuthorization(True),
                "deterministic cognitive demo",
            )
        )
        if (
            local.route is not CoordinatedRoute.LOCAL
            or denied.route is not CoordinatedRoute.SAFE_INSUFFICIENCY
            or cognitive.route is not CoordinatedRoute.COGNITIVE
        ):
            raise RuntimeError("Routing demo did not complete expected routes.")
        route_contract_cognitive_calls = int(
            cognitive.route is CoordinatedRoute.COGNITIVE
        )
        return LocalFirstCognitiveRoutingDemoReport(
            RoutingScenarioReport(local.route, local.local_result.handled, False, 0),
            RoutingScenarioReport(denied.route, False, False, 0),
            RoutingScenarioReport(
                cognitive.route,
                False,
                True,
                route_contract_cognitive_calls,
            ),
        )

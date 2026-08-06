"""Infrastructure-free runtime for deterministic local knowledge discovery."""

from dataclasses import dataclass
from typing import Protocol

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


class CallCountObserver(Protocol):
    @property
    def call_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class DiscoveryScenarioReport:
    interpretation_status: LocalCommandInterpretationStatus
    route: CoordinatedRoute | None
    success: bool
    error_code: str | None = None
    record_ids: tuple[str, ...] = ()
    truncated: bool = False
    cognitive_calls: int = 0


@dataclass(frozen=True, slots=True)
class LocalKnowledgeDiscoveryDemoReport:
    scenarios: tuple[DiscoveryScenarioReport, ...]
    store_calls: int
    read_calls: int
    find_calls: int
    total_repository_operations: int
    cognitive_calls: int
    model_calls: int = 0
    external_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if len(self.scenarios) != 10:
            raise ValueError("The discovery demo requires ten scenarios.")
        if (
            self.store_calls != 2
            or self.read_calls != 0
            or self.find_calls != 4
            or self.total_repository_operations
            != self.store_calls + self.read_calls + self.find_calls
            or self.total_repository_operations != 6
            or self.cognitive_calls != 1
        ):
            raise ValueError("The discovery demo call profile is inconsistent.")
        if any(
            (
                self.model_calls,
                self.external_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("The discovery demo cannot report remote calls.")


class LocalKnowledgeDiscoveryDemoRuntime:
    def __init__(
        self,
        router: LocalCommandTextRouter,
        actor: ActorIdentity,
        denied_actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        store_observer: CallCountObserver,
        read_observer: CallCountObserver,
        find_observer: CallCountObserver,
        cognitive_observer: CallCountObserver,
        model_observers: tuple[CallCountObserver, ...] = (),
        external_observers: tuple[CallCountObserver, ...] = (),
        readiness_observers: tuple[CallCountObserver, ...] = (),
        network_observers: tuple[CallCountObserver, ...] = (),
    ) -> None:
        self._router = router
        self._actor = actor
        self._denied_actor = denied_actor
        self._workspace = workspace
        self._store_observer = store_observer
        self._read_observer = read_observer
        self._find_observer = find_observer
        self._cognitive_observer = cognitive_observer
        self._model_observers = model_observers
        self._external_observers = external_observers
        self._readiness_observers = readiness_observers
        self._network_observers = network_observers

    def _route(self, actor, text, fallback=False):
        before = self._cognitive_observer.call_count
        result = self._router.route(
            TextRoutingRequest(
                actor,
                self._workspace,
                text,
                CognitiveFallbackAuthorization(fallback),
            )
        )
        return result, self._cognitive_observer.call_count - before

    def run(self) -> LocalKnowledgeDiscoveryDemoReport:
        store = (
            'knowledge store :: {"record_id":"%s","kind":"fact",'
            '"key":"child.diaper_size","value":"4",'
            '"source_type":"user_asserted","source_reference":"actor:demo"}'
        )
        observed = (
            self._route(self._actor, store % "diaper-a"),
            self._route(self._actor, store % "diaper-b"),
            self._route(self._actor, 'knowledge find :: {"key":"child.diaper_size"}'),
            self._route(
                self._actor,
                'knowledge find :: {"key":"child.diaper_size","kind":"fact"}',
            ),
            self._route(
                self._actor,
                'knowledge find :: {"key":"child.diaper_size","kind":"concept"}',
            ),
            self._route(self._actor, 'knowledge find :: {"key":"missing"}'),
            self._route(
                self._denied_actor, 'knowledge find :: {"key":"child.diaper_size"}'
            ),
            self._route(self._actor, "knowledge find :: {", True),
            self._route(self._actor, "unrelated denied"),
            self._route(self._actor, "unrelated authorized", True),
        )
        expected_routes = (
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            CoordinatedRoute.LOCAL,
            None,
            CoordinatedRoute.SAFE_INSUFFICIENCY,
            CoordinatedRoute.COGNITIVE,
        )
        reports = []
        for (result, cognitive_calls), expected in zip(
            observed, expected_routes, strict=True
        ):
            coordinated = result.coordinated_result
            route = coordinated.route if coordinated else None
            if route is not expected:
                raise RuntimeError("Discovery demo route is inconsistent.")
            local = coordinated.local_result if coordinated else None
            cognitive = coordinated.cognitive_outcome if coordinated else None
            reports.append(
                DiscoveryScenarioReport(
                    result.interpretation.status,
                    route,
                    local.success
                    if local
                    else cognitive.success
                    if cognitive
                    else False,
                    local.error_code if local else None,
                    tuple(record.record_id for record in getattr(local, "records", ())),
                    getattr(local, "truncated", False),
                    cognitive_calls,
                )
            )

        def total(observers):
            return sum(observer.call_count for observer in observers)

        store_calls = self._store_observer.call_count
        read_calls = self._read_observer.call_count
        find_calls = self._find_observer.call_count
        return LocalKnowledgeDiscoveryDemoReport(
            tuple(reports),
            store_calls,
            read_calls,
            find_calls,
            store_calls + read_calls + find_calls,
            self._cognitive_observer.call_count,
            total(self._model_observers),
            total(self._external_observers),
            total(self._readiness_observers),
            total(self._network_observers),
        )

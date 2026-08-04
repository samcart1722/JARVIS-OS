"""Infrastructure-free runtime for deterministic local knowledge commands."""

from dataclasses import dataclass
from typing import Protocol

from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    KnowledgeRecord,
    WorkspaceIdentity,
)
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRoute,
)


@dataclass(frozen=True, slots=True)
class KnowledgeCommandScenarioReport:
    interpretation_status: LocalCommandInterpretationStatus
    route: CoordinatedRoute | None
    success: bool
    created: bool = False
    error_code: str | None = None
    record: KnowledgeRecord | None = None
    cognitive_calls: int = 0


class CallCountObserver(Protocol):
    @property
    def call_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class LocalKnowledgeCommandDemoReport:
    scenarios: tuple[KnowledgeCommandScenarioReport, ...]
    model_calls: int = 0
    external_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if len(self.scenarios) != 9:
            raise ValueError("The knowledge-command demo requires nine scenarios.")
        if any(
            (
                self.model_calls,
                self.external_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("The knowledge-command demo cannot report remote calls.")


class LocalKnowledgeCommandDemoRuntime:
    def __init__(
        self,
        router: LocalCommandTextRouter,
        actor: ActorIdentity,
        denied_actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        cognitive_observer: CallCountObserver,
        model_observers: tuple[CallCountObserver, ...],
        external_observers: tuple[CallCountObserver, ...],
        readiness_observers: tuple[CallCountObserver, ...],
        network_observers: tuple[CallCountObserver, ...],
    ) -> None:
        self._router = router
        self._actor = actor
        self._denied_actor = denied_actor
        self._workspace = workspace
        self._cognitive_observer = cognitive_observer
        self._model_observers = model_observers
        self._external_observers = external_observers
        self._readiness_observers = readiness_observers
        self._network_observers = network_observers

    def _route(self, actor: ActorIdentity, text: str, allowed: bool = False):
        return self._router.route(
            TextRoutingRequest(
                actor,
                self._workspace,
                text,
                CognitiveFallbackAuthorization(allowed),
            )
        )

    def run(self) -> LocalKnowledgeCommandDemoReport:
        first_store = (
            'knowledge store :: {"record_id":"pair record","kind":"fact",'
            '"key":"demo.key","value":"four","source_type":"user_asserted",'
            '"source_reference":"actor:knowledge-demo-actor"}'
        )
        read_store = first_store.replace("pair record", "read record")
        conflict_store = first_store.replace("pair record", "conflict record")
        conflict = conflict_store.replace('"value":"four"', '"value":"five"')

        def observed(actor: ActorIdentity, text: str, allowed: bool = False):
            before = self._cognitive_observer.call_count
            result = self._route(actor, text, allowed)
            return result, self._cognitive_observer.call_count - before

        first = observed(self._actor, first_store)
        duplicate = observed(self._actor, first_store)
        read_setup = self._route(self._actor, read_store)
        if not read_setup.coordinated_result.local_result.success:
            raise RuntimeError("Knowledge-command read setup failed.")
        read = observed(
            self._actor,
            'knowledge read :: {"record_id":"read record"}',
        )
        conflict_setup = self._route(self._actor, conflict_store)
        if not conflict_setup.coordinated_result.local_result.success:
            raise RuntimeError("Knowledge-command conflict setup failed.")
        results = (
            first,
            duplicate,
            read,
            observed(self._actor, conflict),
            observed(
                self._actor,
                'knowledge read :: {"record_id":"missing"}',
            ),
            observed(
                self._denied_actor,
                first_store.replace("pair record", "denied record"),
            ),
            observed(self._actor, "knowledge store :: {", True),
            observed(self._actor, "unrelated denied text"),
            observed(self._actor, "unrelated authorized text", True),
        )
        expected_routes = (
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
        routes = tuple(
            result.coordinated_result.route
            if result.coordinated_result is not None
            else None
            for result, _ in results
        )
        if routes != expected_routes:
            raise RuntimeError("Knowledge-command demo routes are inconsistent.")
        reports = []
        for result, cognitive_calls in results:
            coordinated = result.coordinated_result
            local = coordinated.local_result if coordinated else None
            cognitive = coordinated.cognitive_outcome if coordinated else None
            success = (
                local.success
                if local
                else cognitive.success
                if cognitive
                else False
            )
            reports.append(
                KnowledgeCommandScenarioReport(
                    result.interpretation.status,
                    coordinated.route if coordinated else None,
                    success,
                    local.created if local else False,
                    local.error_code if local else None,
                    local.record if local and hasattr(local, "record") else None,
                    cognitive_calls,
                )
            )
        def total(observers: tuple[CallCountObserver, ...]) -> int:
            return sum(item.call_count for item in observers)
        return LocalKnowledgeCommandDemoReport(
            tuple(reports),
            model_calls=total(self._model_observers),
            external_calls=total(self._external_observers),
            readiness_calls=total(self._readiness_observers),
            network_calls=total(self._network_observers),
        )

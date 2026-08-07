"""Internal deterministic demonstration of configured trusted-host routing."""

from dataclasses import dataclass
from typing import Protocol

from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.cognition.trusted_context.models import (
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    TrustedHostRequestInput,
    TrustedLocalCommandRequest,
)
from app.cognition.trusted_context.routing import TrustedLocalCommandRoutingService


class CallCountObserver(Protocol):
    @property
    def call_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class TrustedRequestContextScenarioReport:
    scenario_id: str
    passed: bool
    trust_success: bool
    status: str
    items: tuple[str, ...] = ()
    router_calls: int = 0
    permission_calls: int = 0
    repository_calls: int = 0
    cognitive_calls: int = 0


@dataclass(frozen=True, slots=True)
class TrustedRequestContextDemoReport:
    scenarios: tuple[TrustedRequestContextScenarioReport, ...]
    model_calls: int = 0
    provider_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if len(self.scenarios) != 7:
            raise ValueError(
                "The trusted request-context demo requires seven scenarios."
            )
        if any(
            (
                self.model_calls,
                self.provider_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError(
                "The trusted request-context demo cannot use remote calls."
            )

    @property
    def success(self) -> bool:
        return all(scenario.passed for scenario in self.scenarios)


class TrustedRequestContextDemoRuntime:
    def __init__(
        self,
        service: TrustedLocalCommandRoutingService,
        binding_key: str,
        primary_workspace_id: str,
        secondary_workspace_id: str,
        unbound_workspace_id: str,
        denied_workspace_id: str,
        router_observer: CallCountObserver,
        permission_observer: CallCountObserver,
        repository_observers: tuple[CallCountObserver, ...],
        cognitive_observer: CallCountObserver,
        model_observers: tuple[CallCountObserver, ...] = (),
        provider_observers: tuple[CallCountObserver, ...] = (),
        readiness_observers: tuple[CallCountObserver, ...] = (),
        network_observers: tuple[CallCountObserver, ...] = (),
    ) -> None:
        self._service = service
        self._binding_key = binding_key
        self._primary_workspace_id = primary_workspace_id
        self._secondary_workspace_id = secondary_workspace_id
        self._unbound_workspace_id = unbound_workspace_id
        self._denied_workspace_id = denied_workspace_id
        self._router_observer = router_observer
        self._permission_observer = permission_observer
        self._repository_observers = repository_observers
        self._cognitive_observer = cognitive_observer
        self._model_observers = model_observers
        self._provider_observers = provider_observers
        self._readiness_observers = readiness_observers
        self._network_observers = network_observers

    @staticmethod
    def _total(observers: tuple[CallCountObserver, ...]) -> int:
        return sum(observer.call_count for observer in observers)

    def _route(self, binding_key: str, workspace_id: str, text: str):
        before = (
            self._router_observer.call_count,
            self._permission_observer.call_count,
            self._total(self._repository_observers),
            self._cognitive_observer.call_count,
        )
        result = self._service.route(
            TrustedLocalCommandRequest(
                TrustedHostRequestInput(binding_key, workspace_id),
                text,
                CognitiveFallbackAuthorization(False),
            )
        )
        after = (
            self._router_observer.call_count,
            self._permission_observer.call_count,
            self._total(self._repository_observers),
            self._cognitive_observer.call_count,
        )
        return result, tuple(
            end - start for start, end in zip(before, after, strict=True)
        )

    @staticmethod
    def _observed(result) -> tuple[str, tuple[str, ...]]:
        if not result.trust_resolution.success:
            return result.trust_resolution.error_code, ()
        routed = result.text_routing_result
        if routed.interpretation.status is LocalCommandInterpretationStatus.INVALID:
            return routed.interpretation.invalid_reason.value, ()
        local = routed.coordinated_result.local_result
        return local.error_code or "local_success", getattr(local, "items", ())

    def run(self) -> TrustedRequestContextDemoReport:
        requests = (
            (
                "valid-permitted",
                self._binding_key,
                self._primary_workspace_id,
                "list read demo-list",
            ),
            (
                "unknown-binding",
                "unknown-binding-selector",
                self._primary_workspace_id,
                "list read demo-list",
            ),
            (
                "unknown-workspace",
                self._binding_key,
                "workspace-unknown",
                "list read demo-list",
            ),
            (
                "known-unbound-workspace",
                self._binding_key,
                self._unbound_workspace_id,
                "list read demo-list",
            ),
            (
                "explicit-second-workspace",
                self._binding_key,
                self._secondary_workspace_id,
                "list read demo-list",
            ),
            (
                "downstream-permission-denial",
                self._binding_key,
                self._denied_workspace_id,
                "list read demo-list",
            ),
            (
                "payload-workspace-override",
                self._binding_key,
                self._primary_workspace_id,
                'knowledge store :: {"record_id":"record-demo","kind":"fact",'
                '"key":"demo.key","value":"value-demo","source_type":"user",'
                '"source_reference":"actor-demo","workspace":"workspace-secondary"}',
            ),
        )
        expected = (
            (True, "local_success", 1, ("item-alpha",)),
            (False, TRUSTED_CONTEXT_UNKNOWN_BINDING, 0, ()),
            (False, TRUSTED_CONTEXT_UNKNOWN_WORKSPACE, 0, ()),
            (False, TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND, 0, ()),
            (True, "local_success", 1, ("item-beta",)),
            (True, "local_permission_denied", 1, ()),
            (True, "invalid_knowledge_fields", 1, ()),
        )
        reports = []
        for request, expectation in zip(requests, expected, strict=True):
            scenario_id, binding_key, workspace_id, text = request
            result, deltas = self._route(binding_key, workspace_id, text)
            status, items = self._observed(result)
            trust_success, expected_status, expected_router_calls, expected_items = (
                expectation
            )
            passed = (
                result.trust_resolution.success is trust_success
                and status == expected_status
                and deltas[0] == expected_router_calls
                and items == expected_items
                and deltas[3] == 0
            )
            if scenario_id == "downstream-permission-denial":
                passed = passed and deltas[1] == 1
            if scenario_id == "payload-workspace-override":
                passed = passed and deltas[2] == 0
            reports.append(
                TrustedRequestContextScenarioReport(
                    scenario_id,
                    passed,
                    result.trust_resolution.success,
                    status,
                    items,
                    *deltas,
                )
            )
        return TrustedRequestContextDemoReport(
            tuple(reports),
            self._total(self._model_observers),
            self._total(self._provider_observers),
            self._total(self._readiness_observers),
            self._total(self._network_observers),
        )

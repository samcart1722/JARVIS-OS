"""Internal deterministic demonstration of authenticated local routing."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.principal_authentication import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedLocalCommandRoutingService,
    LocalAuthenticationProof,
)


class CallCountObserver(Protocol):
    @property
    def call_count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class LocalPrincipalAuthenticationScenarioReport:
    scenario_id: str
    passed: bool
    status: str
    authentication_success: bool
    mapping_success: bool
    workspace_success: bool
    membership_success: bool
    authenticator_calls: int
    mapper_calls: int
    membership_calls: int
    router_calls: int
    permission_calls: int
    repository_calls: int
    cognitive_calls: int


@dataclass(frozen=True, slots=True)
class LocalPrincipalAuthenticationDemoReport:
    scenarios: tuple[LocalPrincipalAuthenticationScenarioReport, ...]
    model_calls: int = 0
    provider_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if len(self.scenarios) != 8:
            raise ValueError("The authentication demo requires eight scenarios.")
        if any(
            (
                self.model_calls,
                self.provider_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("The authentication demo cannot use remote calls.")

    @property
    def success(self) -> bool:
        return all(scenario.passed for scenario in self.scenarios)


class LocalPrincipalAuthenticationDemoRuntime:
    def __init__(
        self,
        service: AuthenticatedLocalCommandRoutingService,
        valid_proof: object,
        unmapped_proof: object,
        primary_workspace_id: str,
        absent_workspace_id: str,
        inactive_workspace_id: str,
        denied_workspace_id: str,
        authenticator_observer: CallCountObserver,
        mapper_observer: CallCountObserver,
        membership_observer: CallCountObserver,
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
        self._valid_proof = valid_proof
        self._unmapped_proof = unmapped_proof
        self._primary_workspace_id = primary_workspace_id
        self._absent_workspace_id = absent_workspace_id
        self._inactive_workspace_id = inactive_workspace_id
        self._denied_workspace_id = denied_workspace_id
        self._stage_observers = (
            authenticator_observer,
            mapper_observer,
            membership_observer,
            router_observer,
            permission_observer,
        )
        self._repository_observers = repository_observers
        self._cognitive_observer = cognitive_observer
        self._model_observers = model_observers
        self._provider_observers = provider_observers
        self._readiness_observers = readiness_observers
        self._network_observers = network_observers

    @staticmethod
    def _total(observers: tuple[CallCountObserver, ...]) -> int:
        return sum(observer.call_count for observer in observers)

    @staticmethod
    def _status_value(value: object) -> str:
        return str(value.value) if isinstance(value, Enum) else str(value)

    @classmethod
    def _status(cls, result: AuthenticatedLocalCommandRoutingResult) -> str:
        if not result.authentication_result.success:
            return cls._status_value(result.authentication_result.error_code)
        if not result.mapping_result.success:
            return cls._status_value(result.mapping_result.error_code)
        if not result.workspace_selection_result.success:
            return cls._status_value(result.workspace_selection_result.error_code)
        if not result.membership_decision.success:
            return cls._status_value(result.membership_decision.error_code)
        routed = result.text_routing_result
        if routed.interpretation.status is LocalCommandInterpretationStatus.INVALID:
            return cls._status_value(routed.interpretation.invalid_reason)
        return routed.coordinated_result.local_result.error_code or "local_success"

    def _route(self, proof: object, workspace: object, text: object):
        before = (
            *(observer.call_count for observer in self._stage_observers),
            self._total(self._repository_observers),
            self._cognitive_observer.call_count,
        )
        result = self._service.route(
            AuthenticatedLocalCommandRequest(
                LocalAuthenticationProof(proof),
                workspace,
                text,
                CognitiveFallbackAuthorization(False),
            )
        )
        after = (
            *(observer.call_count for observer in self._stage_observers),
            self._total(self._repository_observers),
            self._cognitive_observer.call_count,
        )
        return result, tuple(
            end - start for start, end in zip(before, after, strict=True)
        )

    def run(self) -> LocalPrincipalAuthenticationDemoReport:
        malformed_workspace = object()
        requests = (
            (
                "authenticated-active-permitted",
                self._valid_proof,
                self._primary_workspace_id,
                "list read demo-list",
            ),
            (
                "authentication-failure-precedes-invalid-workspace",
                "unknown-demo-proof",
                malformed_workspace,
                "list read demo-list",
            ),
            (
                "mapping-failure-precedes-invalid-workspace",
                self._unmapped_proof,
                malformed_workspace,
                "list read demo-list",
            ),
            (
                "workspace-selection-invalid",
                self._valid_proof,
                malformed_workspace,
                "list read demo-list",
            ),
            (
                "membership-not-found",
                self._valid_proof,
                self._absent_workspace_id,
                "list read demo-list",
            ),
            (
                "membership-inactive",
                self._valid_proof,
                self._inactive_workspace_id,
                "list read demo-list",
            ),
            (
                "authenticated-active-permission-denied",
                self._valid_proof,
                self._denied_workspace_id,
                "list read demo-list",
            ),
            (
                "authenticated-payload-workspace-override-rejected",
                self._valid_proof,
                self._primary_workspace_id,
                'knowledge store :: {"record_id":"record-demo","kind":"fact",'
                '"key":"demo.key","value":"value-demo","source_type":"user",'
                '"source_reference":"actor-demo","workspace":"workspace-other"}',
            ),
        )
        expected = (
            ("local_success", (1, 1, 1, 1, 1, 1, 0)),
            ("authentication_failed", (1, 0, 0, 0, 0, 0, 0)),
            ("principal_mapping_failed", (1, 1, 0, 0, 0, 0, 0)),
            ("workspace_selection_invalid", (1, 1, 0, 0, 0, 0, 0)),
            ("membership_not_found", (1, 1, 1, 0, 0, 0, 0)),
            ("membership_inactive", (1, 1, 1, 0, 0, 0, 0)),
            ("local_permission_denied", (1, 1, 1, 1, 1, 0, 0)),
            ("invalid_knowledge_fields", (1, 1, 1, 1, 0, 0, 0)),
        )
        reports = []
        for request, expectation in zip(requests, expected, strict=True):
            scenario_id, proof, workspace, text = request
            result, deltas = self._route(proof, workspace, text)
            status = self._status(result)
            expected_status, expected_deltas = expectation
            reports.append(
                LocalPrincipalAuthenticationScenarioReport(
                    scenario_id=scenario_id,
                    passed=status == expected_status and deltas == expected_deltas,
                    status=status,
                    authentication_success=result.authentication_result.success,
                    mapping_success=bool(
                        result.mapping_result and result.mapping_result.success
                    ),
                    workspace_success=bool(
                        result.workspace_selection_result
                        and result.workspace_selection_result.success
                    ),
                    membership_success=bool(
                        result.membership_decision
                        and result.membership_decision.success
                    ),
                    authenticator_calls=deltas[0],
                    mapper_calls=deltas[1],
                    membership_calls=deltas[2],
                    router_calls=deltas[3],
                    permission_calls=deltas[4],
                    repository_calls=deltas[5],
                    cognitive_calls=deltas[6],
                )
            )
        return LocalPrincipalAuthenticationDemoReport(
            tuple(reports),
            self._total(self._model_observers),
            self._total(self._provider_observers),
            self._total(self._readiness_observers),
            self._total(self._network_observers),
        )

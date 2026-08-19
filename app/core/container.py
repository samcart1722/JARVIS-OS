"""
Application Composition Root.

This module is responsible for constructing and wiring the
application services.

It is intentionally simple and framework-independent.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.capabilities.registry import CapabilityRegistry
from app.cognition.classification.default_goal_classifier import (
    DefaultGoalClassifier,
)
from app.cognition.engine import CognitiveEngine
from app.cognition.grounding.claim_formatter import ClaimEvidenceFormatter
from app.cognition.grounding.claim_parser import JsonClaimEvidenceResponseParser
from app.cognition.grounding.claim_provider import ClaimEvidenceAttributionProvider
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.parser import JsonGroundedResponseParser
from app.cognition.grounding.provider import (
    EvidenceBoundedReasoningProvider,
)
from app.cognition.grounding.verification_parser import (
    JsonClaimEvidenceVerificationParser,
)
from app.cognition.grounding.verification_prompt import (
    ClaimEvidenceVerificationPromptBuilder,
)
from app.cognition.grounding.verification_provider import (
    OllamaClaimEvidenceVerifier,
)
from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.interpretation.routing import LocalCommandTextRouter
from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.contracts import (
    KnowledgeRecordRepository,
    ListItemRepository,
)
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.cognition.memory.extractors.default_extractor import DefaultExtractor
from app.cognition.memory.intelligence.default_classifier import (
    DefaultClassifier,
)
from app.cognition.memory.persistence.in_memory_repository import (
    InMemoryRepository,
)
from app.cognition.memory.pipeline.default_memory_pipeline import (
    DefaultMemoryPipeline,
)
from app.cognition.memory.ranking.default_ranker import DefaultRanker
from app.cognition.memory.retrieval.default_retriever import DefaultRetriever
from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
)
from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import ScopedMemoryRecord
from app.cognition.memory.validation.default_validator import (
    DefaultValidator,
)
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.prompts.reasoning import (
    ClaimEvidenceAttributionPromptBuilder,
    EvidenceBoundedReasoningPromptBuilder,
    MemoryAwareReasoningPromptBuilder,
)
from app.cognition.providers.ollama_provider import OllamaProvider
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.specialists.default_specialist import DefaultSpecialist
from app.cognition.specialists.deterministic_reasoning_selection_policy import (
    DeterministicReasoningSelectionPolicy,
)
from app.cognition.specialists.specialist_router import SpecialistRouter
from app.cognition.trusted_context import (
    ConfiguredTrustedHostBinding,
    ConfiguredTrustedRequestContextResolver,
    TrustedLocalCommandRoutingService,
    TrustedRequestContextResolver,
)
from app.core.compatibility.legacy_memory_adapter import LegacyMemoryAdapter
from app.core.config import Settings, settings
from app.membership import (
    ActorWorkspaceMembership,
    InMemoryMembershipRepository,
    MembershipDecisionService,
    MembershipRepository,
)
from app.models.ollama_client import OllamaClient
from app.models.ollama_readiness_probe import OllamaReadinessProbe
from app.principal_authentication import (
    AuthenticatedLocalCommandRoutingService,
    ConfiguredLocalPrincipalAuthenticator,
    ConfiguredPrincipalActorMapper,
    ConfiguredPrincipalActorMapping,
    ConfiguredPrincipalProofBinding,
    LocalPrincipalAuthenticator,
    PrincipalActorMapper,
    PrincipalActorMappingRepository,
    RejectingLocalPrincipalAuthenticator,
    RepositoryPrincipalActorMapper,
)


class Container:
    """
    Central application composition root.

    This class creates and owns long-lived application services.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        *,
        scoped_memory_records: Iterable[ScopedMemoryRecord] = (),
        local_permission_grants: tuple[PermissionGrant, ...] = (),
        local_list_repository: ListItemRepository | None = None,
        local_knowledge_repository: KnowledgeRecordRepository | None = None,
        trusted_host_bindings: tuple[ConfiguredTrustedHostBinding, ...] = (),
        trusted_known_workspaces: tuple[WorkspaceIdentity, ...] = (),
        trusted_request_context_resolver: TrustedRequestContextResolver
        | None = None,
        memberships: tuple[ActorWorkspaceMembership, ...] = (),
        membership_repository: MembershipRepository | None = None,
        principal_proof_bindings: tuple[ConfiguredPrincipalProofBinding, ...] = (),
        principal_actor_mappings: tuple[ConfiguredPrincipalActorMapping, ...] = (),
        principal_actor_mapping_repository: PrincipalActorMappingRepository
        | None = None,
        local_principal_authenticator: LocalPrincipalAuthenticator | None = None,
        principal_actor_mapper: PrincipalActorMapper | None = None,
    ) -> None:
        if isinstance(scoped_memory_records, (str, bytes)):
            raise TypeError("Scoped memory records must be a collection of records.")
        if type(trusted_host_bindings) is not tuple:
            raise ValueError("Trusted host bindings must be a tuple.")
        if type(trusted_known_workspaces) is not tuple:
            raise ValueError("Trusted known workspaces must be a tuple.")
        if type(memberships) is not tuple:
            raise ValueError("Memberships must be a tuple.")
        if type(principal_proof_bindings) is not tuple:
            raise ValueError("Principal proof bindings must be a tuple.")
        if type(principal_actor_mappings) is not tuple:
            raise ValueError("Principal actor mappings must be a tuple.")
        if any(
            type(membership) is not ActorWorkspaceMembership
            for membership in memberships
        ):
            raise ValueError("Configured membership is invalid.")
        if membership_repository is not None and memberships:
            raise ValueError("Membership repository ownership is ambiguous.")
        if any(
            type(binding) is not ConfiguredPrincipalProofBinding
            for binding in principal_proof_bindings
        ):
            raise ValueError("Configured principal proof binding is invalid.")
        if any(
            type(mapping) is not ConfiguredPrincipalActorMapping
            for mapping in principal_actor_mappings
        ):
            raise ValueError("Configured principal actor mapping is invalid.")
        if local_principal_authenticator is not None and principal_proof_bindings:
            raise ValueError("Principal authenticator ownership is ambiguous.")
        if (
            principal_actor_mapping_repository is not None
            and principal_actor_mappings
        ):
            raise ValueError("Principal mapper ownership is ambiguous.")
        if principal_actor_mapper is not None and (
            principal_actor_mappings
            or principal_actor_mapping_repository is not None
        ):
            raise ValueError("Principal mapper ownership is ambiguous.")
        operational_authentication = (
            bool(principal_proof_bindings)
            or local_principal_authenticator is not None
        )
        mapper_configured = (
            bool(principal_actor_mappings)
            or principal_actor_mapping_repository is not None
            or principal_actor_mapper is not None
        )
        if operational_authentication and not mapper_configured:
            raise ValueError("Operational authentication requires a principal mapper.")
        if trusted_request_context_resolver is not None and (
            trusted_host_bindings or trusted_known_workspaces
        ):
            raise ValueError("Trusted resolver ownership is ambiguous.")
        self._settings = app_settings
        self._scoped_memory_records = tuple(scoped_memory_records)
        self._local_permission_grants = local_permission_grants
        self._injected_local_list_repository = local_list_repository
        self._injected_local_knowledge_repository = local_knowledge_repository
        self._trusted_host_bindings = tuple(trusted_host_bindings)
        self._trusted_known_workspaces = tuple(trusted_known_workspaces)
        self._injected_trusted_request_context_resolver = (
            trusted_request_context_resolver
        )
        self._memberships = tuple(memberships)
        self._injected_membership_repository = membership_repository
        self._principal_proof_bindings = tuple(principal_proof_bindings)
        self._principal_actor_mappings = tuple(principal_actor_mappings)
        self._injected_principal_actor_mapping_repository = (
            principal_actor_mapping_repository
        )
        self._injected_local_principal_authenticator = local_principal_authenticator
        self._injected_principal_actor_mapper = principal_actor_mapper
        self._build_memory()
        self._build_local_resolution()
        self._build_reasoning()
        self._build_local_first_cognitive_routing()
        self._build_local_command_interpretation()
        self._build_membership()
        self._build_principal_authentication()
        self._build_trusted_request_context()
        self._build_context()
        self._build_prompt()
        self._build_models()
        self._build_reflection()
        self._build_learning()
        self._build_tools()
        self._build_vision()
        self._build_speech()

    def _build_memory(self) -> None:
        """Compose Cognitive Memory Engine services."""
        self._memory_repository = InMemoryRepository()
        self._memory_extractor = DefaultExtractor()
        self._memory_validator = DefaultValidator()
        self._memory_classifier = DefaultClassifier()
        self._memory_retriever = DefaultRetriever()
        self._memory_ranker = DefaultRanker()

        self.memory_pipeline = DefaultMemoryPipeline(
            repository=self._memory_repository,
            extractor=self._memory_extractor,
            validator=self._memory_validator,
            classifier=self._memory_classifier,
            retriever=self._memory_retriever,
            ranker=self._memory_ranker,
        )
        self.memory = LegacyMemoryAdapter(self.memory_pipeline)
        self.scoped_memory_repository = InMemoryScopedMemoryRepository(
            self._scoped_memory_records
        )
        self.memory_context_retriever = RepositoryMemoryContextRetriever(
            self.scoped_memory_repository
        )
        self.explicit_memory_update_service = ExplicitMemoryUpdateService(
            self.scoped_memory_repository,
            enabled=self._settings.MEMORY_UPDATE_ENABLED,
        )

    def _build_local_resolution(self) -> None:
        """Compose the deterministic local capability path once."""
        self.local_list_repository = (
            self._injected_local_list_repository
            if self._injected_local_list_repository is not None
            else InMemoryListItemRepository()
        )
        self.local_knowledge_repository = (
            self._injected_local_knowledge_repository
            if self._injected_local_knowledge_repository is not None
            else InMemoryKnowledgeRecordRepository()
        )
        self.local_permission_policy = ExplicitPermissionPolicy(
            self._local_permission_grants
        )
        self.structured_list_capability = StructuredListCapability(
            self.local_list_repository,
            self.local_permission_policy,
        )
        self.structured_knowledge_capability = StructuredKnowledgeCapability(
            self.local_knowledge_repository,
            self.local_permission_policy,
        )
        self.local_first_resolver = LocalFirstResolver(
            self.structured_list_capability,
            self.structured_knowledge_capability,
        )

    def _build_reasoning(self) -> None:
        """Compose the Cognitive Engine entry point."""
        self.goal_classifier = DefaultGoalClassifier()
        self.reasoning_selection_policy = DeterministicReasoningSelectionPolicy(
            reasoning_enabled=self._settings.REASONING_ENABLED
        )
        self.default_specialist = DefaultSpecialist(self.reasoning_selection_policy)
        self.specialist_router = SpecialistRouter(self.default_specialist)
        self.normalized_input_capability = NormalizedInputCapability()
        self.ollama_client = OllamaClient(
            base_url=self._settings.OLLAMA_BASE_URL,
            models_url=self._settings.OLLAMA_MODELS_URL,
            model=self._settings.OLLAMA_MODEL,
            timeout_seconds=self._settings.OLLAMA_TIMEOUT_SECONDS,
        )
        self.provider_readiness_probe = OllamaReadinessProbe(self.ollama_client)
        self.memory_evidence_selector = MemoryEvidenceSelector(
            max_records=self._settings.MEMORY_PROMPT_MAX_RECORDS,
            max_characters=self._settings.MEMORY_PROMPT_MAX_CHARACTERS,
        )
        self.memory_aware_reasoning_prompt_builder = MemoryAwareReasoningPromptBuilder(
            memory_context_enabled=(self._settings.MEMORY_PROMPT_CONTEXT_ENABLED),
            max_records=self._settings.MEMORY_PROMPT_MAX_RECORDS,
            max_characters=self._settings.MEMORY_PROMPT_MAX_CHARACTERS,
        )
        grounded_enabled = self._settings.MEMORY_GROUNDED_RESPONSE_ENABLED
        claim_enabled = (
            grounded_enabled
            and self._settings.MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED
        )
        verification_enabled = (
            claim_enabled and self._settings.MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED
        )
        independent_verifier_enabled = (
            verification_enabled
            and self._settings.MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED
        )
        self.grounded_response_parser = None
        self.claim_evidence_response_parser = None
        self.claim_evidence_formatter = None
        self.claim_evidence_verification_parser = None
        self.claim_evidence_verification_prompt_builder = None
        self.claim_evidence_verifier = None
        self.claim_verifier_ollama_client = None
        self.claim_verifier_readiness_probe = None
        if claim_enabled:
            self.reasoning_prompt_builder = ClaimEvidenceAttributionPromptBuilder(
                self.memory_aware_reasoning_prompt_builder,
                self.memory_evidence_selector,
                enabled=True,
            )
        elif grounded_enabled:
            self.reasoning_prompt_builder = EvidenceBoundedReasoningPromptBuilder(
                self.memory_aware_reasoning_prompt_builder,
                self.memory_evidence_selector,
                enabled=True,
            )
        else:
            self.reasoning_prompt_builder = self.memory_aware_reasoning_prompt_builder
        self.ollama_reasoning_provider = OllamaProvider(
            self.ollama_client,
            self.reasoning_prompt_builder,
        )
        if claim_enabled:
            self.claim_evidence_response_parser = JsonClaimEvidenceResponseParser()
            self.claim_evidence_formatter = ClaimEvidenceFormatter()
            if verification_enabled:
                self.claim_evidence_verification_parser = (
                    JsonClaimEvidenceVerificationParser()
                )
                self.claim_evidence_verification_prompt_builder = (
                    ClaimEvidenceVerificationPromptBuilder()
                )
                verifier_client = self.ollama_client
                if independent_verifier_enabled:
                    verifier_base_url = (
                        self._settings.OLLAMA_VERIFIER_BASE_URL
                        if self._settings.OLLAMA_VERIFIER_BASE_URL is not None
                        else self._settings.OLLAMA_BASE_URL
                    )
                    verifier_models_url = (
                        self._settings.OLLAMA_VERIFIER_MODELS_URL
                        if self._settings.OLLAMA_VERIFIER_MODELS_URL is not None
                        else self._settings.OLLAMA_MODELS_URL
                    )
                    verifier_model = (
                        self._settings.OLLAMA_VERIFIER_MODEL
                        if self._settings.OLLAMA_VERIFIER_MODEL is not None
                        else self._settings.OLLAMA_MODEL
                    )
                    verifier_timeout = (
                        self._settings.OLLAMA_VERIFIER_TIMEOUT_SECONDS
                        if self._settings.OLLAMA_VERIFIER_TIMEOUT_SECONDS is not None
                        else self._settings.OLLAMA_TIMEOUT_SECONDS
                    )
                    self.claim_verifier_ollama_client = OllamaClient(
                        base_url=verifier_base_url,
                        models_url=verifier_models_url,
                        model=verifier_model,
                        timeout_seconds=verifier_timeout,
                    )
                    self.claim_verifier_readiness_probe = OllamaReadinessProbe(
                        self.claim_verifier_ollama_client
                    )
                    verifier_client = self.claim_verifier_ollama_client
                self.claim_evidence_verifier = OllamaClaimEvidenceVerifier(
                    verifier_client,
                    self.claim_evidence_verification_prompt_builder,
                    self.claim_evidence_verification_parser,
                )
            self.reasoning_provider = ClaimEvidenceAttributionProvider(
                self.ollama_reasoning_provider,
                self.claim_evidence_response_parser,
                self.memory_evidence_selector,
                self.claim_evidence_formatter,
                self.claim_evidence_verifier,
                enabled=True,
            )
        elif grounded_enabled:
            self.grounded_response_parser = JsonGroundedResponseParser()
            self.reasoning_provider = EvidenceBoundedReasoningProvider(
                self.ollama_reasoning_provider,
                self.grounded_response_parser,
                self.memory_evidence_selector,
                enabled=True,
            )
        else:
            self.reasoning_provider = self.ollama_reasoning_provider
        self.reasoning_stage = ReasoningStage(self.reasoning_provider)
        self.reasoning_capability = ReasoningCapability(self.reasoning_stage)
        self.capability_registry = CapabilityRegistry()
        self.capability_registry.register(
            NORMALIZED_INPUT_CAPABILITY_ID,
            self.normalized_input_capability,
        )
        self.capability_registry.register(
            REASONING_CAPABILITY_ID,
            self.reasoning_capability,
        )
        self.capability_executor = CapabilityExecutor(self.capability_registry)
        self.response_stage = ResponseStage()
        self.cognitive_engine = CognitiveEngine(
            goal_classifier=self.goal_classifier,
            specialist_router=self.specialist_router,
            capability_executor=self.capability_executor,
            response_stage=self.response_stage,
            memory_context_retriever=self.memory_context_retriever,
            memory_retrieval_enabled=self._settings.MEMORY_RETRIEVAL_ENABLED,
        )

    def _build_local_first_cognitive_routing(self) -> None:
        """Compose one explicit coordinator from the existing paths."""
        self.local_first_cognitive_coordinator = LocalFirstCognitiveCoordinator(
            self.local_first_resolver,
            self.cognitive_engine,
        )

    def _build_local_command_interpretation(self) -> None:
        """Compose one deterministic interpreter around the existing coordinator."""
        self.local_command_interpreter = DeterministicLocalCommandInterpreter()
        self.local_command_text_router = LocalCommandTextRouter(
            self.local_command_interpreter,
            self.local_first_cognitive_coordinator,
        )

    def _build_trusted_request_context(self) -> None:
        """Compose trusted context resolution around the existing text router."""
        self.trusted_request_context_resolver = (
            self._injected_trusted_request_context_resolver
            if self._injected_trusted_request_context_resolver is not None
            else ConfiguredTrustedRequestContextResolver(
                self._trusted_host_bindings,
                self._trusted_known_workspaces,
            )
        )
        self.trusted_local_command_routing_service = (
            TrustedLocalCommandRoutingService(
                self.trusted_request_context_resolver,
                self.membership_decision_service,
                self.local_command_text_router,
            )
        )

    def _build_principal_authentication(self) -> None:
        """Compose the authentication-first local command boundary."""
        self.local_principal_authenticator = (
            self._injected_local_principal_authenticator
            if self._injected_local_principal_authenticator is not None
            else (
                ConfiguredLocalPrincipalAuthenticator(self._principal_proof_bindings)
                if self._principal_proof_bindings
                else RejectingLocalPrincipalAuthenticator()
            )
        )
        if self._injected_principal_actor_mapper is not None:
            self.principal_actor_mapper = self._injected_principal_actor_mapper
        elif self._injected_principal_actor_mapping_repository is not None:
            self.principal_actor_mapper = RepositoryPrincipalActorMapper(
                self._injected_principal_actor_mapping_repository
            )
        else:
            self.principal_actor_mapper = ConfiguredPrincipalActorMapper(
                self._principal_actor_mappings
            )
        self.authenticated_local_command_routing_service = (
            AuthenticatedLocalCommandRoutingService(
                self.local_principal_authenticator,
                self.principal_actor_mapper,
                self.membership_decision_service,
                self.local_command_text_router,
            )
        )

    def _build_membership(self) -> None:
        """Compose one deterministic membership decision boundary."""
        self.membership_repository = (
            self._injected_membership_repository
            if self._injected_membership_repository is not None
            else InMemoryMembershipRepository(self._memberships)
        )
        self.membership_decision_service = MembershipDecisionService(
            self.membership_repository
        )

    def _build_context(self) -> None:
        """Compose context services."""
        pass

    def _build_prompt(self) -> None:
        """Compose prompt services."""
        pass

    def _build_models(self) -> None:
        """Compose model services."""
        pass

    def _build_reflection(self) -> None:
        """Compose reflection services."""
        pass

    def _build_learning(self) -> None:
        """Compose learning services."""
        pass

    def _build_tools(self) -> None:
        """Compose tool services."""
        pass

    def _build_vision(self) -> None:
        """Compose vision services."""
        pass

    def _build_speech(self) -> None:
        """Compose speech services."""
        pass


container = Container()

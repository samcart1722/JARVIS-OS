# Cognitive Core — Active Components

Status: **Executable baseline v1**
Evidence checkpoint: Sprint 11 working tree based on `f843842`

## Purpose

The Cognitive Core coordinates a user objective through context creation,
classification, specialist planning, logical capability selection, capability
execution, and response formatting. It owns cognitive sequencing and internal
contracts. It does not own HTTP transport, deployment configuration, provider
construction, model hosting, network clients, or product-specific behavior.

An AI model is not the Core. Ollama is replaceable infrastructure behind
`ReasoningProvider`; the active default path does not invoke it.

## Scope and boundaries

- **Cognitive components:** modules under the active portions of
  `app/cognition` listed below.
- **Contracts:** protocols and abstract contracts for classification,
  specialists, selection, capabilities, and reasoning providers.
- **Composition:** `app/core/container.py` and `app/core/config.py`; outside the
  Core.
- **Infrastructure:** `OllamaProvider` and `OllamaClient`; outside the Core.
- **HTTP boundary:** `app/api/routes/brain.py`; outside the Core.
- **Legacy:** historical modules explicitly listed in [Legacy code](#legacy-code).

The cognitive memory implementation under `app/cognition/memory` is composed
for compatibility but does not participate in `CognitiveEngine.process`.

## Trusted request-context components

The released Sprint 27 `app/cognition/trusted_context` package owns the
transport-neutral trusted request-context models, resolver port, configured
resolver, and trusted local routing service.

| Component | Responsibility | Ownership and boundary |
|---|---|---|
| `TrustedRequestContextResolver` | Resolves a host input to an immutable actor/workspace context or stable trust failure. | Internal port; no transport, persistence, provider, or authorization ownership. |
| `ConfiguredTrustedRequestContextResolver` | Performs deterministic lookup against immutable process configuration. | Trusted-context implementation; no runtime mutation or default workspace. |
| `TrustedLocalCommandRoutingService` | Resolves trust, short-circuits failure, then delegates to the existing text router. | Supported internal application boundary; does not authenticate public HTTP. |
| `Container` composition | Owns one resolver and one trusted routing service while reusing the existing `LocalCommandTextRouter`. | Composition Root; injected and configured resolver ownership cannot be mixed. |

These components do not alter `CognitiveEngine`. `PermissionPolicy` remains
downstream authorization.

## Canonical active flow

```text
POST /brain/think?prompt=...
  -> module-level Container
  -> CognitiveEngine.process(user_input)
  -> Goal + CognitiveContext
  -> DefaultGoalClassifier -> Domain.UNKNOWN
  -> SpecialistRouter -> DefaultSpecialist
  -> ReasoningSelectionPolicy
  -> Plan -> PlanStep(capability_id)
  -> CapabilityExecutor
  -> CapabilityRegistry
  -> NormalizedInputCapability | ReasoningCapability
  -> CapabilityResult -> ExecutionResult
  -> ResponseStage
  -> CognitiveOutcome
  -> HTTP mapper
  -> {success, prompt, input, response, error}
```

The reasoning branch, when explicitly enabled, is:

```text
ReasoningCapability
  -> ReasoningStage
  -> ReasoningProvider
  -> OllamaProvider
  -> OllamaClient
```

## Component catalog

| Component | Responsibility and I/O | Allowed dependencies | Prohibited dependencies | Status |
|---|---|---|---|---|
| `CognitiveEngine` | `str -> CognitiveOutcome`; creates goal/context and sequences collaborators. | Internal classifier, router, executor, response stage, domain models. | FastAPI, Settings, concrete providers/clients, HTTP status codes. | Stable orchestration boundary. |
| `Goal` | Immutable user objective description. | Standard library only. | Infrastructure and transport. | Stable model. |
| `CognitiveContext` | Immutable request context passed through planning/execution. | `Goal`, standard library. | Settings, FastAPI, concrete infrastructure. | Stable model; lifecycle fields remain provisional. |
| `DefaultGoalClassifier` | `CognitiveContext -> Domain`; currently always `UNKNOWN`. | Classifier contract and domain models. | Infrastructure and product rules. | Provisional. |
| `Domain` | Enumerates available domain labels. | Standard library. | Infrastructure. | Provisional values. |
| `SpecialistRouter` | `Domain -> Specialist`; maps every domain to the injected default specialist. | Domain and specialist contract. | Settings, providers, clients. | Provisional routing. |
| `Specialist` | Contract for support check and context-based plan creation. | Goal, context, plan. | Infrastructure. | Active contract. |
| `DefaultSpecialist` | Calls selection once and creates one `PlanStep`. | Context, plan models, selection contract. | Settings, providers, Ollama, I/O. | Provisional planner. |
| `ReasoningSelectionPolicy` | `CognitiveContext -> capability_id`. | Context only. | Settings, providers, registry, I/O. | Active contract. |
| `DeterministicReasoningSelectionPolicy` | Selects an official ID solely from `reasoning_enabled`. | Context and capability IDs. | Prompt heuristics and infrastructure. | Stable v1 policy. |
| `Plan` | Immutable ordered tuple of steps. | `PlanStep`. | Infrastructure. | Stable model. |
| `PlanStep` | Immutable `id`, `description`, and logical `capability_id`. | Standard library. | Capability instances and providers. | Stable v1 model; empty ID compatibility remains. |
| `Capability` | `execute(context, step) -> CapabilityResult`. | Internal context/result/step models. | HTTP response construction. | Active contract. |
| `CapabilityRegistry` | Registers unique logical IDs and resolves capabilities. | Capability contract for typing. | Plan interpretation and execution. | Stable v1. |
| `CapabilityExecutor` | Executes ordered plan steps and aggregates results. | Registry and planning/result models. | Concrete providers, Settings, FastAPI. | Stable v1, sequential/fail-fast. |
| `NormalizedInputCapability` | Returns `context.normalized_input`. | Capability contract and internal models. | Network, models, memory. | Deterministic bootstrap capability. |
| `ReasoningCapability` | Converts canonical reasoning output into capability output. | Capability contract, `ReasoningStage`, internal models. | Concrete provider/client construction. | Active, opt-in. |
| `CapabilityResult` | Per-capability success, outputs, internal errors, optional structured error code, metadata. | Standard library. | Infrastructure. | Stable v1 result with structured failure propagation. |
| `ExecutionResult` | Aggregated plan success, completed steps, outputs, internal errors, structured error code, metadata. | Standard library. | Infrastructure. | Stable v1 result with structured failure propagation. |
| `CognitiveError` | Stable provider-independent code and safe cognitive message. | Standard library. | FastAPI, providers, HTTP status codes. | Stable v1 domain model. |
| `CognitiveOutcome` | Enforces exclusive success-with-response or failure-with-error state. | `CognitiveError`, standard library. | FastAPI, providers, HTTP status codes. | Stable v1 final Core result. |
| `ReasoningStage` | Calls one injected `ReasoningProvider`. | Provider contract and reasoning models. | Concrete client construction. | Active invocation boundary. |
| `ReasoningProvider` | `generate(context) -> ReasoningResult`. | Internal context/result models. | Settings and HTTP transport. | Active replaceable port. |
| `ResponseStage` | Maps `ExecutionResult` to `CognitiveOutcome` without inspecting error text. | Execution result and outcome models. | Capabilities, providers, FastAPI, HTTP construction/status. | Active structured boundary. |
| `BrainResponse` / HTTP mapper | Preserves prompt/input/response, adds success/error, and maps known cognitive codes to HTTP. | FastAPI, public API models, `CognitiveOutcome` codes. | Provider internals and raw execution errors. | Public transport boundary outside Core. |
| `Container` | Constructs, registers, and injects all active runtime dependencies. | Settings, Core components, concrete infrastructure. | Per-request cognitive decisions and execution. | Composition Root, outside Core. |
| `Settings` | Validates application/Ollama settings and reasoning enablement. | Pydantic settings. | Cognitive decisions. | Operational configuration, outside Core. |
| `OllamaProvider` | Implements `ReasoningProvider` using an injected client. | Provider port, internal models, `OllamaClient`. | Settings and capability selection. | Infrastructure. |
| `OllamaClient` | Performs configured HTTP generation on `chat`; construction is inert. | `requests`. | Core orchestration. | Infrastructure. |

## Composition Root

`Container` translates operational settings into concrete objects. It builds
the Ollama client/provider path, selection policy, default specialist, router,
both registered capabilities, executor, response stage, and engine. It
registers `normalized_input` and `reasoning` independently of selection.

`Container` must not classify requests, select a capability during a request,
execute a plan, or format a cognitive response. Its scaffolded `_build_*`
methods containing `pass` do not represent active functionality.

## Permitted extensions

- **Capability:** implement `Capability`, define one logical ID, construct and
  register it in `Container`, and let a specialist request only its ID.
- **Provider:** implement `ReasoningProvider` and inject it into the existing
  reasoning stage from `Container`.
- **Policy:** implement `ReasoningSelectionPolicy` and inject it into the
  specialist from `Container`.
- **Specialist:** implement `Specialist`, then extend the existing router
  composition explicitly. No specialist registry/factory beyond current code
  is claimed.

These are extension directions, not implemented dynamic discovery.

## Legacy code

The public cognitive route does not use:

- `app/brain` (`Brain`, legacy `Orchestrator`, planners and classifiers);
- historical `app/reasoning`;
- historical `app/context`;
- historical `app/memory`;
- `app/prompt`, handlers, tools, reflection, and response managers;
- tests under `app/tests`, excluded by configured pytest `testpaths`.

These modules remain present and may have internal historical consumers. They
are neither deleted nor represented as part of the canonical public runtime.

## Known gaps

Classification, routing, and planning are provisional. There is no task
builder, evidence lifecycle, automatic lifecycle memory update, provider
availability policy,
retry, fallback, streaming, replanning, parallel execution, or rich structured
public response. The normative Cognitive Lifecycle is therefore broader than
the executable baseline.

## Operational readiness outside the Core

`ProviderReadinessResult` is an immutable safe operational model and
`ProviderReadinessProbe.check()` is its replaceable contract.
`OllamaReadinessProbe` uses the injected `OllamaClient` to list models once.
`ReasoningDemoRuntime` gates the already-composed engine behind explicit
enablement and readiness. These components are outside the Cognitive Core and
public API; construction and normal cognitive requests do not trigger them.

## Scoped memory persistence foundation

Sprint 12 added a parallel, read-only foundation under
`app/cognition/memory/scoped`. `MemoryScope` is an explicit immutable opaque
identifier. `ScopedMemoryRecord` owns immutable content within one scope.
`ScopedMemoryRepository` requires scope on every search, and the in-memory
implementation indexes constructor records by scope.

Later sprints compose this separate scoped subsystem without copying global or
legacy memory. Global and legacy memory remain unchanged and separate.

## Controlled memory context integration

Sprint 13 activates only the scoped read path. `MemorySnapshot` distinguishes
retrieval not executed (`None`) from an executed empty scoped result.
`MemoryContextRetriever` is the Core-facing read-only contract and
`RepositoryMemoryContextRetriever` adapts `ScopedMemoryRepository`.

`Container` composes an empty `InMemoryScopedMemoryRepository` and injects its
retriever into `CognitiveEngine`. The engine retrieves only when the feature is
enabled and an explicit `MemoryScope` is supplied, before classification. The
same enriched immutable context then reaches specialist planning, capability
execution, and reasoning-provider contracts.

The public API and historical single-run demo supply no scope. Sprint 15's
functional comparison supplies an explicit ephemeral scope only to its
memory-aware engine.

## Memory-aware reasoning prompt policy

Sprint 14 adds `ReasoningPromptBuilder`, an exact-compatibility builder, and a
bounded memory-aware builder. OllamaProvider receives the contract by
injection and performs no retrieval.

Without usable enabled memory, normalized input is returned byte-for-byte.
Otherwise a stable prompt separates the request, JSON-serialized untrusted
scoped records, safety text, and response instruction. Record-count and
source-content character limits are deterministic.

## Functional cognitive demo

Sprint 15 adds `FunctionalCognitiveDemoRuntime` outside the public API. It
checks readiness exactly once, then runs the same prompt through isolated
baseline and memory-aware engines. The CLI constructs explicit, ephemeral
records under one required `MemoryScope`. Baseline memory is disabled; scoped
retrieval and prompt memory are enabled only for the comparison path. No demo
record is persisted. Its immutable report exposes only safe readiness,
positive record count, an explicit-scope boolean, and structured outcomes; it
never stores the scope or infrastructure details.

## Explicit scoped memory update

Sprint 16 adds the separate `ScopedMemoryWriter` port and
`ExplicitMemoryUpdateService`. The in-memory repository implements ordered,
scope-owned append while retaining the read contract. Exact duplicates are
allowed.

Container injects the same repository into the retriever and update service.
Update enablement is independent and false by default. Writes occur only
through deliberate `remember(scope, content)` calls; construction, retrieval,
reasoning, prompt building, readiness, provider execution, and the public API
remain write-free.

`ExplicitMemoryUpdateDemoRuntime` is operational infrastructure outside the
Core. It checks readiness once, executes before, performs ordered explicit
writes, and executes after with the same prompt and scope. Its immutable report
stores safe counts, readiness, and outcomes without scope or content.

## Evidence-bounded reasoning

Sprint 17 adds immutable grounding envelopes and selected-evidence models, a
pure deterministic selector, a strict JSON parser, an evidence-bounded prompt
builder, and a `ReasoningProvider` decorator. The builder and decorator share
one selector policy. `OllamaProvider` remains responsible only for prompt
transport and one model invocation.

When grounding is disabled or selected evidence is empty, the historical
provider result is returned exactly. When active, valid answers expose only
stable selected-record numbers; insufficient evidence produces deterministic
safe text; invalid protocol produces a controlled cognitive failure.

`GroundedReasoningDemoRuntime` is operational infrastructure outside the
public API. It gates two isolated engines behind one readiness check and stores
no scope, prompt, record content, or raw provider response.

Sprint 18 adds pure claim models, parser, formatter, prompt policy, and one
provider decorator. Container activates that path only when both flags are on.

Sprint 19 adds immutable verdict models, strict parser, pure cited-evidence
prompt serialization, and one Ollama-backed verifier before claim formatting.
The prompt builder and provider share a selector instance but independently
recompute selection over the same immutable snapshot.

Sprint 20 lets Container inject either the primary client or one separately
configured verifier client into the existing verifier adapter.
Verifier settings are optional overrides; absent values inherit primary
configuration by value without mutating Settings.

## Sprint 28 membership components

`app/membership` owns immutable models, `MembershipRepository`, the in-memory
implementation, and `MembershipDecisionService`. `SQLiteLocalStorage` is the
outward durable implementation. Trusted routing requires membership before
text routing. Container defaults to in-memory and accepts caller-owned durable
injection. The durable demo is an operations proof, not authentication or RBAC.


## Sprint 29 local principal authentication components

`app/principal_authentication` owns the transport-neutral local authentication
models, authenticator and mapper ports, configured process-local
implementations, and `AuthenticatedLocalCommandRoutingService`.

The authenticated application path is deliberately separate from the Sprint 27
trusted-binding path. Authentication produces a `PrincipalIdentity`; explicit
principal-to-actor mapping produces an `ActorIdentity`; only then is workspace
selected and membership evaluated. `PermissionPolicy` remains downstream
action authorization.

`Container` is the sole composition root for the authenticated routing service.
Configured authentication and mapping are local development/test/demo
facilities and contain no durable credential technology.

## Sprint 30 durable principal-actor mapping released components

The Sprint 30 release at `governed-sprint-30-complete` adds durability only to the
`PrincipalIdentity -> ActorIdentity` association.

`PrincipalActorMappingRepository` is the Core-facing persistence port.
`RepositoryPrincipalActorMapper` adapts that port to the existing
`PrincipalActorMapper` contract. Neither owns authentication, workspace
selection, membership, or action authorization.

`SQLitePrincipalActorMappingRepository` is the outward infrastructure adapter
backed by `SQLiteLocalStorage`. SQLite schema v3 adds only the
`principal_actor_mappings` table with exact case-sensitive `principal_id` and
non-null `actor_id`.

`Container` accepts explicit repository injection and constructs
`RepositoryPrincipalActorMapper` only when that repository is the selected
mapping source. Configured mappings, an explicitly injected mapper, and an
injected mapping repository are mutually exclusive ownership choices.
Default composition remains configured-empty/no-I/O.

The durable principal-actor demo is operational proof outside the public API.
It persists mappings in one process, reopens them in another, and demonstrates
authenticated local routing with zero model, provider, readiness, or network
calls.

The release adds no credential/proof persistence, public authentication API,
session, role, permission, workspace, membership, token, or account-lifecycle
storage. `CognitiveEngine`, the trusted route, membership semantics, and
`PermissionPolicy` remain unchanged.

## Sprint 31 governed durable action-permission components

The governed Sprint 31 release preserves PermissionPolicy as the Core-facing
authorization boundary and adds one optional repository-backed implementation.

PermissionGrantRepository owns exact lookup and append-only creation for one
actor/workspace/action grant. It is a Core-facing contract and owns no SQLite,
transport, authentication, membership, role, or runtime behavior.

RepositoryPermissionPolicy adapts that repository to the existing
PermissionPolicy contract. Missing grants and declared repository failures deny
access.

SQLitePermissionGrantRepository is the outward infrastructure adapter over an
explicitly owned SQLiteLocalStorage instance.

SQLite schema v4 stores exact actor_id, workspace_id, and action values only.
It is not RBAC, credential storage, or permission-history storage.

Container selects either the existing configured ExplicitPermissionPolicy or an
explicitly injected repository-backed policy. Default construction remains
no-I/O.

The same composed permission policy continues to be shared by the structured
list and structured knowledge capabilities; Sprint 31 does not create a second
authorization path.

The durable action-permission runtime remains an operations proof outside the
public API and CognitiveEngine.

These components remain released at `governed-sprint-31-complete`; formal
Sprint 31 governance closure was subsequently completed at canonical checkpoint
`fa90defc44ad756a33f11e470105db57a440e201`.

## Sprint 33 governed revocation components

Sprint 33 adds the separate `PermissionGrantRevocationRepository` port while
preserving the historical `PermissionGrantRepository` lookup/create surface.

`SQLitePermissionGrantRepository` is the sole production SQLite adapter with
the combined structural shape `__init__`, `is_granted`, `create`, and `revoke`.
Its `revoke` method delegates to caller-owned `SQLiteLocalStorage`, which
validates the exact key and performs one physical exact `DELETE` from
`action_permission_grants`. Present and absent rows share the same committed
`None` result; row count and prior existence are not exposed.

`RepositoryPermissionPolicy` remains authorization-only and invokes only
`is_granted`. It does not depend on or invoke the revocation port. Container
continues to compose permission authorization through the grant repository and
does not construct, store, or expose revocation management.

Schema version remains 4. No soft-delete state, audit history, revoker identity,
expiry, role data, schema object, or migration was added. The Sprint 33
revocation runtime is a separate operations proof outside API, local-command,
authentication, membership, routing, and cognitive execution.

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
builder, evidence lifecycle, memory update, provider availability policy,
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

Sprint 12 adds a parallel, read-only foundation under
`app/cognition/memory/scoped`. `MemoryScope` is an explicit immutable opaque
identifier. `ScopedMemoryRecord` owns immutable content within one scope.
`ScopedMemoryRepository` requires scope on every search, and the in-memory
implementation indexes constructor records by scope.

It is not composed by `Container` or consumed by the engine, context,
capabilities, providers, readiness, demo, or API. Global and legacy memory
remain unchanged and separate.

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

The public API and demo supply no scope. Ollama continues to use only
`normalized_input`; no memory content enters its prompt.

# Cognitive Core — Dependency Rules

Status: **Enforced baseline v1**
Scope: explicit active runtime files only; legacy modules are excluded.

## General rule

Dependencies point toward internal contracts and models. Concrete
infrastructure may implement internal ports, but infrastructure details must
not flow into cognitive domain, specialist, planning, or capability-selection
code.

## API

The active route `app/api/routes/brain.py` may import FastAPI and the already
composed module-level `container`. It delegates to
`container.cognitive_engine.process`.

The API owns the mapping from stable cognitive error codes to HTTP status
codes and public models. It must discard internal execution/provider error
text and expose only the canonical safe cognitive message.

It must not import or construct:

- `OllamaClient` or `OllamaProvider`;
- concrete capabilities;
- `ReasoningSelectionPolicy` implementations;
- `DefaultSpecialist`.

## Composition Root

`app/core/container.py` may know Settings, all active Core contracts and
implementations, concrete providers, and concrete clients. It is the one
construction boundary.

It must not classify a request, select a capability during request execution,
execute plans, or format cognitive responses. Scaffolded `pass` methods do not
represent active services.

## Cognitive domain

Files under active `app/cognition/domain` must not import:

- FastAPI;
- `app.core`, Settings, or Container;
- concrete providers;
- Ollama or `app.models`;
- environment access.
- HTTP status codes or public API models.

Domain models may depend on standard-library types and other internal models.

## Specialists and policies

Active specialist and selection files may depend on `CognitiveContext`, `Goal`,
`Plan`, `PlanStep`, internal contracts, and official logical capability IDs.

They must not depend on:

- Settings or Container;
- FastAPI;
- concrete providers or clients;
- Ollama;
- network/filesystem access.

The deterministic policy does not inspect prompt content or provider
availability.

## Planning and execution

`CapabilityExecutor` may depend on `CapabilityRegistry`, plan/result models,
and context for typing. It must not depend on concrete providers,
`OllamaClient`, Settings, Container, or FastAPI.

Execution policy is sequential and fail-fast; changing that policy requires
explicit architecture review and tests.

## Capabilities

Capabilities may depend on internal contracts, context, plan steps, result
models, and an existing internal stage/port where demonstrated.

They must not construct concrete providers, read environment variables,
construct HTTP responses, or select specialists. The active
`ReasoningCapability -> ReasoningStage -> ReasoningProvider` dependency is
allowed; `ReasoningCapability -> OllamaProvider` is prohibited.

## Providers and infrastructure

`ReasoningProvider` is an internal port. `OllamaProvider` is infrastructure
that implements it and may depend on `OllamaClient`. The client may depend on
the HTTP library and performs I/O only from `chat`.

Configuration enters concrete infrastructure through `Container`; provider
and client modules do not read Settings or environment variables directly.

## Explicit prohibited imports

For the active files guarded by architecture tests:

| Source | Prohibited import prefixes |
|---|---|
| Selection policy contract/implementation | `app.core`, `app.models`, `app.cognition.providers`, `fastapi`, `requests`, `os` |
| `DefaultSpecialist` | `app.core`, `app.models`, `app.cognition.providers`, `fastapi`, `requests`, `os` |
| `CapabilityExecutor` | `app.core`, `app.models`, `app.cognition.providers`, `fastapi`, `requests` |
| Public brain route | `app.models`, `app.cognition.providers`, concrete capability and specialist implementation modules |
| Cognitive domain files | `app.core`, `app.models`, `app.cognition.providers`, `fastapi`, `requests`, `os` |

The enforcement list is intentionally short and explicit. It does not scan the
whole repository or impose new rules on legacy code.

## Exceptions and debt

- `ReasoningCapability` imports `ReasoningStage`; this is an active internal
  boundary, not a concrete-infrastructure leak. The stage imports the provider
  port.
- `Container` also composes cognitive memory and a legacy adapter, but memory is
  absent from `CognitiveEngine.process`.
- `app/cognition/pipeline` still contains input/context stages not called by the
  active engine.
- `PlanStep.capability_id` retains an empty compatibility default.
- Controlled execution failures map structurally to safe non-200 HTTP
  responses at the API boundary.
- Classification and routing are fallback/provisional.

These are documented realities. The rules above do not claim they are
resolved.

## Legacy exclusion

Architecture enforcement excludes historical `app/brain`, `app/reasoning`,
`app/context`, `app/memory`, handlers, prompt managers, and `app/tests`.
Applying active-Core rules indiscriminately to those modules would misrepresent
their migration status.

## Operational readiness and demo

The readiness contract/result under `app/operations` is outside the Cognitive
Core and imports neither cognition, Settings, Container, FastAPI, requests,
nor environment access. The concrete Ollama probe may use an injected client
and request exception types but never generation.

`Container` composes and exposes the probe without calling `check()`.
`CognitiveEngine` and the public brain route do not import or call readiness.
The demo service may depend on the readiness contract and existing engine and
outcome types; only its thin CLI adapter constructs Settings and Container.

## Scoped memory persistence foundation

Scoped models and contract may depend only on their own internal models and
standard-library facilities. They must not import Settings, FastAPI,
reasoning, readiness, legacy memory, or concrete persistence.

The in-memory scoped implementation must not wrap or import the global
`InMemoryRepository` or `LegacyMemoryAdapter`. Until reviewed integration,
API, engine, context, Container, Ollama, readiness, and demo must not consume
scoped memory.

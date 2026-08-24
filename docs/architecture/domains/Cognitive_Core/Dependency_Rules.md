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

## Trusted request-context boundary

`app/cognition/trusted_context` remains independent of API/transport,
infrastructure, persistence, SQL, Settings/environment, providers, model
clients, network, clock, randomness, operations, authentication libraries, and
product domains.

Lower-level interpretation, routing, and local-resolution code must not depend
back on configured trusted-host composition. Public API code and
`CognitiveEngine` do not own or silently invoke the Sprint 27 path.

`TrustedLocalCommandRoutingService` may depend on the existing
`LocalCommandTextRouter`. Production/application local text-command routing
uses the trusted service. Direct `TextRoutingRequest` construction is approved
only in that service and these three historical low-level operation demos:
`local_command_interpretation_demo_runtime.py`,
`local_knowledge_command_demo_runtime.py`, and
`local_knowledge_discovery_demo_runtime.py`. Low-level use remains valid in
tests and explicit internal composition. `LocalCommandTextRouter` is not
private.

`PermissionPolicy` remains downstream authorization. `Container` is the
composition owner for one trusted resolver and service. Standard-library
architecture tests enforce these import, direction, isolation, and constructor
rules.

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
`InMemoryRepository` or `LegacyMemoryAdapter`. API, context, Ollama, and
readiness must not consume scoped-memory persistence. The engine may use the
read-only contract, Container may compose the implementation, and the Sprint
15 CLI may inject synthetic records through Container's narrow parameter.

## Reasoning prompt policy

Prompt builders may depend on `CognitiveContext` and standard-library
serialization. They must not import Settings, Container, FastAPI, OllamaClient,
repositories, retrievers, legacy memory, readiness, environment, or I/O.

OllamaProvider may depend on the prompt-builder contract and client, but must
not retrieve memory. Container alone translates Settings into the concrete
builder. API, engine, memory retriever, readiness, DefaultSpecialist, and
CapabilityExecutor do not construct or import prompt builders.

## Active memory-context integration

`CognitiveContext` may depend on `MemorySnapshot`. `CognitiveEngine` may depend
on the `MemoryContextRetriever` contract and scoped domain models, but not on
the in-memory implementation, legacy adapter, Settings, or storage.

`RepositoryMemoryContextRetriever` depends on `ScopedMemoryRepository`, never
its concrete implementation. `Container` alone may compose the concrete empty
repository and inject the feature flag. API, OllamaProvider, readiness,
DefaultSpecialist, and CapabilityExecutor must not import scoped-memory
infrastructure. Memory and readiness remain independent.

## Functional demo boundary

The comparison runtime may depend on the engine, outcome, scope, and readiness
contracts, but not Settings, Container, FastAPI, environment access, requests,
or concrete providers. Its thin CLI adapter may compose Settings, Container,
and scoped domain records. The public API remains unaware of the demo.

## Explicit scoped memory update boundary

`ScopedMemoryWriter` depends only on scoped domain records. The explicit update
service may depend on that port and scoped models, but not Settings, Container,
FastAPI, Ollama, readiness, legacy memory, environment access, or I/O.

The in-memory repository may implement both separate read and write ports.
Container alone injects its one instance into retriever and update service.
Engine, provider, prompt builder, retriever, readiness, public API, and Sprint
15 demo must not import or invoke the update service.

`ExplicitMemoryUpdateDemoRuntime` may depend on the engine, update service,
scope models, outcomes, and readiness contract. It must not construct Settings,
Container, concrete repository, provider, client, capability, specialist, or
registry. Only its thin CLI adapter composes Settings and Container.

## Evidence-bounded reasoning boundary

Grounding models, selector, and parser are pure Core support and may depend
only on domain context/snapshot models and the standard library. The parser
must not know engines, providers, Settings, Container, FastAPI, repositories,
Ollama, readiness, environment, or I/O.

The evidence-bounded prompt builder may depend on the prompt contract,
`CognitiveContext`, selector, and standard-library serialization. The provider
decorator may depend on `ReasoningProvider`, reasoning models, selector, and
parser. Neither may depend on Settings, Container, FastAPI, repositories,
retrievers, legacy memory, concrete clients, readiness, filesystem, or
database.

Container alone selects historical or grounded composition and shares the
selector policy between builder and decorator. OllamaProvider remains unaware
of parsing. The API must not import grounding modules or expose scope.

`GroundedReasoningDemoRuntime` may depend on engine, outcome, scope, and
readiness contracts, but not Settings, Container, FastAPI, repositories,
concrete providers, clients, environment, or I/O. Its thin CLI owns local
composition only.

Claim models have no infrastructure dependencies. The claim parser, formatter,
provider, and demo runtime retain explicit inward-facing boundaries; Engine,
API, and readiness do not import claim modules.

Verification models/parser/prompt remain infrastructure-free. Only the adapter
knows OllamaClient; Container composes it and Engine/API remain unaware.

Container alone may construct the independent verifier client and readiness
probe. Operations runtime consumes probes and engines only.

## Sprint 28 membership boundary

`app/membership` may use standard library, sibling modules, and only
`ActorIdentity`/`WorkspaceIdentity` from local-resolution models. It cannot
depend on permissions, routing, Container, SQLite, API, authentication,
providers, or networking. SQLite remains outward infrastructure. Public API
and `CognitiveEngine` do not own membership.


## Sprint 29 local principal authentication boundary

`app/principal_authentication` may depend on its own contracts/models and the
minimum existing identity, workspace, membership, and text-routing contracts
needed by authenticated orchestration. It must not own SQLite, FastAPI,
credential transport, provider/networking, membership persistence, or
`PermissionPolicy` implementation.

`Container` alone composes
`AuthenticatedLocalCommandRoutingService`. Public API and `CognitiveEngine` do
not construct or invoke this authenticated local route.

## Sprint 30 durable principal-actor mapping released boundary

The `governed-sprint-30-complete` release preserves the following boundary.

The Core-facing principal-actor repository contract and
`RepositoryPrincipalActorMapper` remain under `app/principal_authentication`
and must not import `sqlite3` or concrete local-storage infrastructure.

Dependency direction preserves the inward Core boundary:

```text
Core mapping side:

RepositoryPrincipalActorMapper
        |
        v
PrincipalActorMappingRepository

Infrastructure side:

SQLitePrincipalActorMappingRepository
        |
        v
SQLiteLocalStorage
        |
        v
principal-authentication contracts/models
```

The two adapter paths are separate.
`SQLitePrincipalActorMappingRepository` does not depend on
`RepositoryPrincipalActorMapper`.

`app/infrastructure/local_storage` may depend inward on
`PrincipalIdentity`, `ActorIdentity`, and principal-actor repository errors and
contracts needed to implement persistence. Core principal-authentication code
must not depend outward on SQLite.

SQLite principal-actor storage must not import or own authenticators,
authentication proofs, authenticated routing services, workspace selection,
membership decisions, permissions, providers, networking, or public API
transport.

Only `Container` may construct `RepositoryPrincipalActorMapper` for application
composition. Explicit repository injection must perform no I/O at Container
construction beyond retaining and wiring the caller-owned object.

Public HTTP, `CognitiveEngine`, and the Sprint 27 trusted route remain unaware
of durable principal-actor mapping infrastructure.

The durable demo may explicitly construct local SQLite infrastructure because it
is an operations proof. Its CLI remains thin and delegates to the operations
runtime; it does not import SQLite, Container, or cognition modules directly.

## Sprint 31 governed durable action-permission boundary

The dependency direction remains inward:

Structured capability -> PermissionPolicy.

RepositoryPermissionPolicy implements that boundary by depending on
PermissionGrantRepository.

SQLitePermissionGrantRepository is outward infrastructure and depends on
SQLiteLocalStorage plus inward local-resolution contracts/models.

app/cognition/local_resolution must not import sqlite3 or concrete local
storage. Container may depend on PermissionGrantRepository and
RepositoryPermissionPolicy but must not import SQLitePermissionGrantRepository.

Authentication and membership domains do not own permission persistence.
Authentication identifies a principal, principal mapping resolves an actor,
membership admits actor/workspace participation, and PermissionPolicy remains
the separate action-authorization boundary.

Configured permission grants and an injected repository are mutually exclusive
composition sources. Falsey injected repositories are preserved through
explicit is-not-None selection. Default Container composition performs no
repository or filesystem I/O.

The durable action-permission demo remains under operations and is absent from
public HTTP and CognitiveEngine. Its CLI delegates to the operations runtime
instead of constructing SQLite or cognitive components itself.

Architecture tests enforce these governed implementation boundaries. They are
released at `governed-sprint-31-complete`; final release-truth governance
closure remains pending.

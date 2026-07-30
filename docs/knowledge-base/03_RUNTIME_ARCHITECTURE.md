# Runtime Architecture

This document describes the active runtime after Sprint 11, based on the
working tree at `f843842`.

## Public path and flow

```text
POST /brain/think?prompt=...
        |
        v
app.api.routes.brain:think
        |
        v
module-level Container instance -> CognitiveEngine
        |
        v
user_input
  -> Goal + CognitiveContext
  -> DefaultGoalClassifier -> Domain.UNKNOWN
  -> SpecialistRouter -> DefaultSpecialist
  -> Plan(one PlanStep requiring "normalized_input")
  -> CapabilityExecutor(context, plan)
  -> CapabilityRegistry -> NormalizedInputCapability
  -> CapabilityResult -> ExecutionResult
  -> ResponseStage -> normalized request input
```

The public HTTP input is a `prompt` query parameter. The output preserves
`prompt`, `input`, and nullable `response`, and adds `success` and nullable
`error`. The Core entry point is
`CognitiveEngine.process(user_input: str) -> CognitiveOutcome`.

## Stage responsibilities

| Stage | Runtime responsibility |
|---|---|
| `CognitiveEngine` | Owns sequencing; directly constructs goal/context and coordinates dependencies. |
| `DefaultGoalClassifier` | Discards context and returns the fallback domain. |
| `SpecialistRouter` | Resolves all domains to the same default specialist. |
| `DefaultSpecialist` | Builds a provisional one-step plan requesting `normalized_input`. |
| `CapabilityRegistry` | Resolves logical identifiers to implementations composed by `Container`. |
| `CapabilityExecutor` | Runs steps sequentially, passes context and step to capabilities, aggregates results, and fails fast. |
| `NormalizedInputCapability` | Returns normalized context input deterministically; it performs no reasoning. |
| `ReasoningCapability` | Converts the canonical provider-backed `ReasoningStage` result into `CapabilityResult`; available only when a plan requests `reasoning`. |
| `ReasoningSelectionPolicy` | Contract `select_capability(context) -> str`; independent of Settings, providers, registry, and I/O. |
| `DeterministicReasoningSelectionPolicy` | Returns an official identifier solely from immutable `reasoning_enabled`. |
| `ReasoningStage` | Canonical single invocation boundary from `CognitiveContext` to `ReasoningProvider.generate`. |
| `OllamaProvider` | Receives an explicitly configured `OllamaClient`; it performs network I/O only when reasoning executes. |
| `ResponseStage` | Converts execution state to validated `CognitiveOutcome`; it does not know HTTP or parse internal error text. |
| API mapper | Converts known cognitive codes to safe public models and HTTP 500/503; it never exposes raw execution/provider errors. |

## Dependencies and composition

`app/core/container.py` is the Composition Root. `_build_reasoning()` constructs
and registers `NormalizedInputCapability` and `ReasoningCapability`. `Container`
reads official `Settings`, constructs `OllamaClient` with the configured URL,
model, and timeout, and injects it into `OllamaProvider`. Construction does not
perform network I/O. The Container constructs `CapabilityExecutor`
with the shared registry, then injects it and the other stages into
`CognitiveEngine`.

`Container` also translates `REASONING_ENABLED` into
`DeterministicReasoningSelectionPolicy`, injects it into `DefaultSpecialist`,
and injects that specialist into `SpecialistRouter`.
The module creates a module-level `container`; the FastAPI route consumes its
`cognitive_engine` without rebuilding dependencies. `_build_memory()` separately composes
the cognitive memory pipeline and a `LegacyMemoryAdapter`.

## Core boundaries

The active Core path is primarily `app/cognition`, with composition in
`app/core/container.py`. FastAPI is outside that Core. Legacy `app/brain` is
also outside the Core and no longer participates in the public cognitive path.
The engine depends on classifier/specialist contracts and concrete executor and
response-stage classes. Plans reference only stable logical capability
identifiers. No product-specific HealthBridge logic appears in this path.

## Execution policy v1

Execution is sequential and ordered. A step is completed only after its
capability returns `success=True`. Outputs and metadata are aggregated. Missing
capabilities produce a failed `ExecutionResult`; controlled failure preserves
prior successful work and stops the plan. Unexpected exceptions propagate to
the existing HTTP 500 handling. An empty plan succeeds with no completed work
or output.

## Reasoning capability path

Structured execution uses the stable codes `capability_not_found`,
`capability_execution_failed`, and `empty_capability_output`. The API maps the
first to HTTP 500 and the latter two to HTTP 503; success remains HTTP 200.
Unexpected exceptions continue through existing HTTP 500 handling.

An explicit plan step with `capability_id="reasoning"` executes:

`CapabilityRegistry → ReasoningCapability → ReasoningStage →
ReasoningProvider.generate → ReasoningResult → CapabilityResult`

Valid non-empty provider text becomes the capability output. Empty or
whitespace-only text becomes a controlled failure. Unexpected provider
exceptions propagate through the executor to existing HTTP error handling.
`DefaultSpecialist` still requests `normalized_input`, so the public default
path remains deterministic and does not call Ollama.

## Provider configuration boundary

`Settings → Container → OllamaClient(base_url, model, timeout_seconds) →
OllamaProvider(client) → ReasoningStage → ReasoningCapability`

Defaults preserve prior behavior:

- `OLLAMA_BASE_URL=http://localhost:11434/api/generate`
- `OLLAMA_MODELS_URL=http://localhost:11434/api/tags`
- `OLLAMA_MODEL=llama3.2:3b`
- `OLLAMA_TIMEOUT_SECONDS=120`

Pydantic Settings provides environment overrides and rejects timeout values
less than one. Cognitive Core contracts and capabilities do not import Settings
or read environment variables.

## Deterministic selection policy

Disabled/default flow:

`REASONING_ENABLED=false → policy → normalized_input → deterministic output`

Enabled flow:

`REASONING_ENABLED=true → policy → reasoning → ReasoningCapability →
ReasoningStage → ReasoningProvider`

The policy does not inspect prompt text, domain, registry, provider health, or
network availability. The same boolean always produces the same identifier.
Enabling reasoning permits provider execution but does not prove provider
availability. There is no automatic fallback to `normalized_input`.

## Documented versus executable lifecycle

The normative Cognitive Lifecycle includes Task Builder, Task, Workspace,
capabilities, evidence, reasoning/tools during execution, replanning, and Memory
Update. Sprint 6 makes provider-backed reasoning executable when explicitly
requested, but it is not the default public policy and still has no Task
Builder, evidence model, tools, replanning, or memory update.

`InputStage`, `ContextStage`, and provider-backed `ReasoningStage` exist from
Sprint 1 but are bypassed by the current engine implementation. They must not be
described as active stages.

## Legacy and alternative modules

- `app/brain` remains in the repository but its `Brain` and `Orchestrator`
  classes are disconnected from the public cognitive operation.
- `app/memory`, `app/reasoning`, `app/context`, `app/prompt`, and related
  managers predate or sit outside the current `app/cognition` boundary.
- `app/tests` contains an older test suite not collected by the configured
  pytest `testpaths`.
- The memory pipeline under `app/cognition/memory` is composed but not connected
  to `CognitiveEngine.process`.

These paths are recorded, not deprecated or removed by this recovery task.

## Operational readiness and controlled demo

Readiness is separate from cognition:

`Settings -> Container -> OllamaClient -> OllamaReadinessProbe.check()
-> ProviderReadinessResult`

`OLLAMA_BASE_URL` retains its actual historical meaning: the complete
generation endpoint. Separately configured `OLLAMA_MODELS_URL` avoids fragile
string replacement and defaults to Ollama's non-generative `GET /api/tags`.
One response checks server reachability and configured-model presence.

Nothing checks readiness at import, construction, or on the public API path.
Connection/timeout, absent-model, and malformed-content conditions become
safe `provider_unavailable`, `model_unavailable`, and `invalid_response`
states. No raw response or exception is exposed.

Sprint 15 replaces the historical single-run command with the comparison in
[`FUNCTIONAL_COGNITIVE_DEMO.md`](../operations/FUNCTIONAL_COGNITIVE_DEMO.md).

Disabled reasoning performs neither readiness nor engine execution. Enabled
reasoning checks once and only `ready` reaches the Container-composed engine.
Existing `CognitiveOutcome` failures remain distinct from readiness failures.
There is no fallback.

## Scoped memory persistence foundation

The engine-integration audit found that the composed global repository returns
every active record and carries no ownership. Sprint 12 adds a separate,
inactive foundation:

`MemoryScope -> ScopedMemoryRecord -> ScopedMemoryRepository
-> InMemoryScopedMemoryRepository`

Construction groups records by scope. Search first looks up the requested
scope's bucket, then applies a case-insensitive literal substring match.
Results preserve constructor order and are immutable tuples.

The repository consumes no legacy data. Unowned records remain incompatible
pending an explicit migration policy. There is no I/O, write surface,
migration, Container wiring, engine/context change, configuration, prompt use,
demo use, or API change.

## Controlled scoped retrieval

`MEMORY_RETRIEVAL_ENABLED` defaults to false. Container composes:

`InMemoryScopedMemoryRepository(()) -> RepositoryMemoryContextRetriever
-> CognitiveEngine`

Disabled or enabled without scope:

`base CognitiveContext(memory_snapshot=None) -> classifier -> existing flow`

Enabled with explicit scope:

`base context -> retrieve(scope, normalized_input) -> MemorySnapshot
-> enriched frozen context -> classifier -> specialist -> capability`

Retrieval happens exactly once before classification. Empty snapshots continue
normally; cross-scope snapshots are rejected; unexpected failures propagate.
The composed repository starts empty and is not durable.

The HTTP route calls the engine without scope, so it does not retrieve memory.
The functional demo is the sole local adapter that supplies synthetic scoped
records. Legacy data is not copied.

## Governance baseline

The executable runtime is now catalogued in:

- [`Components.md`](../architecture/domains/Cognitive_Core/Components.md);
- [`Contracts.md`](../architecture/domains/Cognitive_Core/Contracts.md);
- [`Dependency_Rules.md`](../architecture/domains/Cognitive_Core/Dependency_Rules.md).

Architecture tests use AST inspection over an explicit active-file list. They
protect selection-policy, specialist, executor, public-route, and cognitive
domain import boundaries. Separate tests require essential document sections
and the active flow/infrastructure distinction. Legacy directories are
deliberately outside this enforcement scope.

## Memory-aware reasoning prompt

Container composes `MemoryAwareReasoningPromptBuilder` into OllamaProvider.
Prompt memory defaults off independently from retrieval. Disabled policy,
missing snapshot, or empty snapshot returns normalized input unchanged.

Enabled matching records produce stable request, untrusted-memory, and
response sections. Records are JSON strings in snapshot order. Record count
is limited first; combined source content is truncated sequentially to the
character budget. The request is not truncated and scope identifier is
omitted. Safety text marks records as untrusted reference data; this is not
complete injection prevention. Provider and API perform no retrieval; the
functional demo's memory-aware engine invokes the configured retriever.

## Functional cognitive demo

The explicit local Sprint 15 demo performs:

`one readiness check -> baseline engine(prompt) -> memory engine(prompt, scope)`

It requires a scope, at least one synthetic record, and a prompt. Two
independent containers use copied Settings. Baseline memory is disabled;
memory-aware execution receives only ephemeral scoped records. Results are
printed separately, including stable failures. Public HTTP behavior remains
unchanged.

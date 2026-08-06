# Runtime Architecture

## Deterministic knowledge discovery (Sprint 26 canonical master)

The existing interpreter, router, coordinator, resolver, knowledge capability,
authorization policy, and repository instances carry a new typed
`FindKnowledgeRecordsQuery`. Authorization with `knowledge.records.read`
precedes one exact repository lookup. Repositories order matching records by
case-sensitive record ID and return at most 51; the capability exposes at most
50 plus `truncated`. Zero results are handled local success and never fall back
to cognition. This feature is canonical at merge commit
`54e04261933ab85dbe4b237e6f81037d508b4a1c`; release tag
`sprint-26-complete` is pending, and Sprint 25.1 remains the latest completed
tagged release until tagging.

## Deterministic knowledge commands (Sprint 25)

The existing `DeterministicLocalCommandInterpreter` accepts strict JSON
`knowledge read` and `knowledge store` commands and constructs the existing
typed knowledge intents. `LocalCommandTextRouter` supplies the request workspace
to interpretation exactly once; workspace cannot be supplied by JSON.
Caller-supplied provenance is preserved in the immutable `KnowledgeRecord`.
Malformed recognized knowledge commands are terminal before coordination.

This is structured deterministic parsing, not natural-language understanding.
The existing coordinator, resolver, capability and repositories are reused.
Public HTTP, `CognitiveEngine`, Settings, SQLite schema and providers are
unchanged.

## Deterministic text interpretation (Sprint 24)

`Container` composes one `DeterministicLocalCommandInterpreter` and one
`LocalCommandTextRouter` after, and using, its existing Sprint 23 coordinator.
The interpreter executes nothing. Valid list text becomes an existing typed
intent; invalid list syntax stops before resolver/coordinator/cognition; other
text passes an immutable unrecognized sentinel through the unchanged resolver.
Only explicit fallback authorization permits the existing cognitive route.
The original text is preserved as cognitive input.

The supported grammar is limited to `list read <list_id>` and
`list add <list_id> :: <item> [| <item> ...]`. The deterministic interpreter
accepts this already bounded command syntax. This deliberately narrow grammar
is not general natural-language understanding: it performs no fuzzy matching,
ambiguity resolution, multilingual interpretation, conversational context,
model-assisted classification, or semantic inference. Malformed text beginning
with the `list` command namespace is `invalid` and terminal; unrelated text is
`not_interpreted`, and cognitive fallback remains explicit and
caller-authorized.

The public HTTP route does not import or invoke text routing. No Settings,
provider, HTTP, SQLite, infrastructure, readiness, or network dependency enters
the interpretation/routing boundary. The existing `CognitiveEngine` is not
modified.

## Explicit local-first coordinator (Sprint 23)

`Container` composes one `LocalFirstCognitiveCoordinator` after its existing
`LocalFirstResolver` and `CognitiveEngine`. The coordinator calls the resolver
exactly once. Handled local success and controlled failure select `local` and
are terminal. Unsupported local intent selects `safe_insufficiency` unless the
caller supplies explicit fallback authorization and valid non-blank cognitive
input; only then does it call the existing processor once and select
`cognitive`.

The coordinator depends on a `CognitiveProcessor` Protocol and imports no
SQLite, infrastructure, HTTP framework, network client, provider, or demo. It
is absent from `CognitiveEngine` and the public API route. The cognitive route
can remain deterministic when existing settings select normalized input; route
selection does not claim model use.

## Local-first route (Sprints 21–22)

Typed list and knowledge intents enter `LocalFirstResolver`. Separate focused
capabilities authorize before calling infrastructure-independent repository
Protocols. Default composition uses in-memory repositories. The durable demo
injects explicitly opened and initialized SQLite storage.

SQLite schema v1 contains `schema_metadata`, `list_items`, and
`knowledge_records`. List identity and order are workspace/list scoped;
knowledge identity is `workspace_id + record_id`. The adapter lives under
`app/infrastructure/local_storage/`; `app/cognition` does not import it.

`ActorIdentity + WorkspaceIdentity + typed intent` flows through
`LocalFirstResolver`, explicit permission policy, `StructuredListCapability`,
and one workspace/list-scoped in-memory repository. Authorization precedes all
repository access. Handled success, denial, and validation failure are terminal
local outcomes and never fall through to Ollama. `CognitiveEngine` remains
unchanged and available as the separate reasoning orchestrator.

These are two distinct entry paths. The public HTTP route calls
`CognitiveEngine`; it does not expose `LocalFirstResolver`. The typed resolver
does not extract natural-language intents and returns `not_handled` for an
unsupported object. Sprint 21 and Sprint 22 added no automatic fallback or
resolve-or-reason bridge. Sprint 23 provides an explicit caller-invoked
`LocalFirstCognitiveCoordinator`, but it is not automatic and public HTTP does
not use it. `CognitiveEngine` itself contains no fallback routing.

Independent verifier mode composes a second inert `OllamaClient` only when all
four feature flags are active. Generation remains primary; verification uses
the secondary client sequentially with no fallback.

With grounding, claim attribution, and verification enabled, one structured
claim envelope is verified once against only its cited bounded evidence before
the existing deterministic formatter runs.

With both grounding and claim attribution enabled, Container selects one claim
protocol path. Historical and Sprint 17 composition remain unchanged.

Sprint 25.1 at `9a61d53a3db036c4399e4fa5eef5e31ee92e6462`, tag
`sprint-25.1-release-closure`, recorded 680 passing tests. Sprint 26 is now
canonical on `master` at merge commit
`54e04261933ab85dbe4b237e6f81037d508b4a1c`; its release tag
`sprint-26-complete` remains pending.

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

## Explicit scoped memory update

`MEMORY_UPDATE_ENABLED` defaults to false independently from retrieval and
prompt context. Container composes one `InMemoryScopedMemoryRepository` shared
by the read-only `RepositoryMemoryContextRetriever` and
`ExplicitMemoryUpdateService` through the separate `ScopedMemoryWriter`
contract.

The Sprint 16 local runtime performs:

`readiness -> before(prompt, scope) -> ordered explicit writes
-> after(prompt, scope)`

Readiness runs once. Failed readiness performs no cognition or write. Each
successful `remember(scope, content)` appends exactly one record; duplicates
are preserved. The after execution retrieves from the same ephemeral
repository. There is no automatic write from engine, provider, prompt builder,
retriever, readiness, or API, and no persistence or legacy-memory access.

## Evidence-bounded memory reasoning

With `MEMORY_GROUNDED_RESPONSE_ENABLED=false`, or without selected evidence,
the historical memory-aware prompt and provider result remain exact.

With the flag enabled and a non-empty scoped snapshot:

`CognitiveContext -> shared MemoryEvidenceSelector
-> EvidenceBoundedReasoningPromptBuilder -> OllamaProvider (one call)
-> EvidenceBoundedReasoningProvider -> strict JSON parser
-> validated ReasoningResult`

The prompt exposes numbered untrusted records but never scope. The parser
accepts one exact envelope, validates references against the same selected
range, and performs no repair. Answered responses add a stable record-number
footer; insufficient evidence uses deterministic text; invalid protocol
becomes a safe structured failure with no raw-response fallback.

The operational comparison uses one readiness check, then standard and
grounded engines once each with identical prompt, scope, and synthetic
records. This is structural grounding and auditability, not semantic fact
verification.

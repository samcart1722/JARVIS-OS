# Current State

## Sprint 25 executable state

Sprint 25 is completed through merged PR #24 at
`1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`
(annotated tag object `6e0de87b426e4a7d4c3103bdffc77f2b171aa30f`).
The existing interpreter maps strict JSON knowledge commands
to existing typed knowledge intents. Workspace comes from the routing request,
not text; caller-supplied provenance is preserved. Malformed recognized
knowledge commands are terminal. Public HTTP and `CognitiveEngine` are unchanged.

This boundary is not broad natural-language understanding or a model
classifier. A cognitive route also does not imply model execution when the
existing settings choose the deterministic cognitive capability.

## Sprint 23 released foundation

Sprint 23 is released at merge `be59175c201df1f2458551d99e2f5dcc3e9d2aac`,
tag `sprint-23-complete`. One explicit coordinator calls `LocalFirstResolver`
first. A handled
local result is terminal. Only `not_handled` plus explicit authorization and a
valid non-blank cognitive input invokes the existing cognitive path.

The coordinator accepts already-typed intents and is not called by public HTTP.
No natural-language parser or automatic bridge was added to `CognitiveEngine`.

The repository now contains an ephemeral, workspace-scoped structured-list
capability with explicit actor and deny-by-default permission policy. Typed add
and read intents resolve deterministically with model/external call counts of
zero. `LocalFirstResolver` returns `not_handled` for unsupported typed intents;
the pre-existing reasoning path remains separately available, but no automatic
bridge chooses between them.
This supersedes older checkpoint counts below as current operational truth;
those figures remain historical evidence.

> Sprint 20 optionally separates generator and verifier client configuration;
> shared-client Sprint 19 behavior remains the default.

> Sprint 19 optionally applies one model-assisted, all-or-nothing claim support
> gate. It does not prove truth or factual accuracy.

> Sprint 18 adds opt-in structural references per claim while preserving the
> historical and Sprint 17 paths. It does not verify semantic support.

Snapshot updated: **2026-08-03** (America/Tegucigalpa).

## Repository checkpoint

- Canonical branch: `master`
- Canonical released HEAD: `1f2da9cfb60a06cb323f30f200720be6437e10a9`
- Canonical released tag: `sprint-25-complete`
- Sprint 25 state: completed, merged through PR #24, and tagged.
- Sprint 26 state: not started.

## Confirmed stack

- Python project requiring Python `>=3.12`; verification ran on Python 3.14.6.
- FastAPI, Pydantic, pydantic-settings, and Loguru are runtime dependencies.
- pytest, pytest-cov, Ruff, and Pyright are declared development dependencies.
- setuptools/wheel build backend.
- The active repository name/package metadata still says `JARVIS-OS` /
  `jarvis-os`; this conflicts with the verified Luxiom product identity.

Source: `pyproject.toml`, `app/main.py`, and `app/core/config.py`.

## Main structure

- `app/cognition/`: current Cognitive Core models, contracts, pipeline pieces,
  memory implementation, and integrated engine.
- `app/core/container.py`: composition root for memory and the cognitive engine.
- `app/brain/`, `app/memory/`, `app/reasoning/`: older application paths still
  present; `app/brain` bridges the HTTP route to the new engine.
- `app/api/`: FastAPI routes.
- `tests/`: configured pytest suite for the current sprints.
- `app/tests/`: legacy tests present but excluded by configured `testpaths`.
- `docs/`: foundation, architecture, RFC, implementation, and recovery material.

## Sprint status

| Sprint | State | Confirmed result |
|---|---|---|
| 0 | Completed/tagged | Cognitive engine entry point and legacy memory compatibility restored. |
| 1 | Completed/tagged | Minimal cognitive pipeline and replaceable reasoning-provider contract added. |
| 2 | Completed/tagged | Core goal, context, domain, specialist, plan, executor, and capability contracts added; Product North Star and Cognitive Lifecycle added. |
| 3 | Completed/tagged | Executable classification → specialist → plan → execution → response flow wired in `Container` and tested. |
| 4 | Completed/tagged | Public cognitive input calls the Container-composed `CognitiveEngine`; behavioral API tests verify the boundary. |
| 5 | Completed/tagged | Capability Runtime v1 resolves and executes a registered deterministic capability. |
| 6 | Completed/tagged | Provider-backed `ReasoningCapability` is executable on demand without changing default policy. |
| 7 | Completed/tagged | Ollama URL, model, and timeout use validated settings and explicit composition. |
| 8 | Completed/tagged | Deterministic policy selects normalized input or reasoning from explicit enablement. |
| 9 | Completed/tagged | Active Core documentation and architecture enforcement protect executable boundaries. |
| 10 | Completed/tagged | Structured outcomes and safe HTTP failure mapping are integrated. |
| 11 | Completed/tagged | Explicit Ollama readiness and controlled opt-in reasoning demo were added outside Core/API. |
| 12 | Completed/tagged | Scoped in-memory repository contracts enforce ownership and isolation. |
| 13 | Completed/tagged | Optional scoped retrieval enriches context only when enabled and explicitly scoped. |
| 14 | Completed/tagged | Bounded memory-aware prompt policy preserves exact default behavior. |
| 15 | Completed/tagged | Controlled baseline/scoped-memory comparison demo proves isolated behavior. |
| 16 | Completed/tagged | Explicit opt-in scoped writes support a controlled ephemeral demo. |
| 17 | Completed/tagged | Evidence-bounded reasoning validates a strict envelope and bounded references. |
| 18 | Completed/tagged | Claim-level evidence attribution adds structurally auditable references. |
| 19 | Completed/tagged | Model-assisted claim support verification remains optional and controlled. |
| 20 | Completed/tagged | Independent verifier-client composition remains opt-in. |
| 21 | Completed/tagged | Released at `8c0330b`, tag `sprint-21-complete`; typed local lists add explicit identity, workspace, permissions and zero-call deterministic execution. |
| 22 | Completed/tagged | Released at `9dcb36b`, tag `sprint-22-complete`; explicit SQLite adapters persist typed lists and minimal provenance-bearing knowledge. |
| 23 | Completed/tagged | Released at merge `be59175c201df1f2458551d99e2f5dcc3e9d2aac`, tag `sprint-23-complete`; explicit typed local-first coordination remains outside public HTTP and `CognitiveEngine`. |
| 24 | Completed/tagged | Released at merge `fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`; bounded list-command interpretation remains outside public HTTP. |
| 25 | Completed/tagged | Released through PR #24 at merge `1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`; strict JSON knowledge commands reuse the existing local-first interpretation and routing path. |

## Executable components and status

| Component | Classification | Evidence |
|---|---|---|
| `CognitiveEngine.process` | Integrated | Constructs `Goal`/`CognitiveContext`, classifies, routes, plans, executes, and formats. |
| `Container` | Integrated, partially scaffolded | Builds memory and cognitive engine; several `_build_*` methods are `pass`. |
| `DefaultGoalClassifier` | Provisional | Always returns `Domain.UNKNOWN`. |
| `SpecialistRouter` | Provisional | Maps every domain to one `DefaultSpecialist`. |
| `DefaultSpecialist` | Provisional | Creates one step requesting the logical `normalized_input` capability. |
| `CapabilityRegistry` | Integrated v1 | Maps stable logical identifiers to injected implementations and detects duplicate or missing identifiers. |
| `CapabilityExecutor` | Integrated v1 | Executes registered capabilities sequentially with context and fail-fast behavior. |
| `NormalizedInputCapability` | Integrated bootstrap capability | Deterministically returns normalized context input; performs no reasoning and uses no external service. |
| `ReasoningCapability` | Integrated, opt-in | Uses `ReasoningStage` and the `ReasoningProvider` port; registered but not selected by `DefaultSpecialist`. |
| `DeterministicReasoningSelectionPolicy` | Integrated | Selects one official capability identifier from immutable boolean enablement; it does not inspect prompts or providers. |
| `DefaultSpecialist` | Policy-driven | Receives `CognitiveContext`, delegates selection once, and constructs the same one-step plan shape. |
| `OllamaProvider` | Composed, not publicly activated | Receives a configured `OllamaClient`; construction performs no network call. |
| Ollama settings | Integrated | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and positive `OLLAMA_TIMEOUT_SECONDS` support environment overrides. |
| Cognitive Core governance docs | Complete for active v1 runtime | Components, contracts, Core/infrastructure boundaries, legacy exclusions, and known debt are documented. |
| Architecture tests | Integrated | Protect explicit active-file import, composition, documentation, and local-resolution boundaries using the standard library. |
| `CognitiveOutcome` / `CognitiveError` | Integrated | Enforce valid success/failure states and stable provider-independent errors. |
| `ResponseStage` | Integrated structured boundary | Returns real output as success or a structured controlled failure; it knows no HTTP. |
| Cognitive memory pipeline | Implemented and composed | Built in `Container`, exposed through a legacy adapter, but absent from the integrated request cycle. |
| Concrete capabilities | Integrated in separate paths | `NormalizedInputCapability` and `ReasoningCapability` remain in the historical engine. Separate `StructuredListCapability` and `StructuredKnowledgeCapability` serve typed local intents outside `CognitiveEngine` and public HTTP. |
| `LocalFirstCognitiveCoordinator` | Composed, explicit application boundary | Preserves handled local results; only authorized valid `not_handled` requests call the existing cognitive processor. Public HTTP does not use it. |
| `DeterministicLocalCommandInterpreter` | Implemented, bounded application interpretation | Maps only the narrow list-command grammar to existing typed intents; it is not general natural-language understanding. |
| `LocalCommandTextRouter` | Composed, explicit application boundary | Invokes the existing Sprint 23 coordinator for bounded commands. Public HTTP and `CognitiveEngine` do not use this service. |
| `InputStage` / `ContextStage` / `ReasoningStage` | Implemented separately | Not called by the Sprint 3 `CognitiveEngine.process` path. |

## Real request flow

The FastAPI `/brain/think` route obtains the already-composed engine from the
module-level `Container` instance and calls
`container.cognitive_engine.process` directly. The engine runs:

`user_input → Goal + CognitiveContext → Domain → Specialist → Plan →
CapabilityRegistry → NormalizedInputCapability → CapabilityResult →
ExecutionResult → ResponseStage → str`

See [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md) for exact boundaries.

## Tests

Command: `.\.venv\Scripts\python.exe -m pytest`

Sprint 25 release validation: **680 passed** with `DEBUG=true`, including **85
focused tests**; Ruff and `git diff --check` passed using controlled external
Sprint 25 pytest temporary directories.

Historical Sprint 24 feature-tree result: **625 passed** with `DEBUG=true`;
Ruff and `git diff --check` passed using a controlled external pytest temporary
directory. Sprint 24 was subsequently released at
`fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`.

Historical Sprint 23 feature-tree result: **591 passed** with `DEBUG=true`;
Ruff and `git diff --check` passed using controlled external pytest temporary
files. Sprint 23 was subsequently released at
`be59175c201df1f2458551d99e2f5dcc3e9d2aac`, tag `sprint-23-complete`.

Sprint 22 released baseline result: **570 passed** with `DEBUG=true`; Ruff and
`git diff --check` passed.

Sprint 21 baseline result: **534 passed** with `DEBUG=true`; Ruff and
`git diff --check` passed. The older counts below are historical checkpoints.

Sprint 4 baseline: **9 passed, 1 warning in 0.14s**.

Sprint 5 baseline: **12 passed, 1 warning in 0.96s**.

Sprint 6 baseline: **24 passed, 1 warning in 0.86s**.

Sprint 7 baseline: **34 passed, 1 warning in 1.05s**.

Sprint 8 baseline: **45 passed, 1 warning in 1.05s**; Ruff passed and
`git diff --check` was clean.

Sprint 9 baseline: **63 passed, 1 warning in 0.87s**; Ruff and
`git diff --check` passed.

Sprint 9 final result: **70 passed, 1 warning in 1.10s** with `DEBUG=true`.
The warning remains the pre-existing pytest cache-path warning. Seven new
tests protect confirmed boundaries and minimum governance-document coverage.
Tests under `app/tests/` remain excluded.

Sprint 10 baseline: **70 passed, 1 warning in 1.69s**; Ruff and
`git diff --check` passed. Final Sprint 10 results are recorded in its summary.

Sprint 11 baseline: **86 passed, 1 warning in 1.84s**; Ruff and
`git diff --check` passed. Readiness uses one on-demand `GET /api/tags`;
construction and the default API path remain network-free.

Sprint 12 baseline: **111 passed, 1 warning in 1.36s**. The scoped foundation
is deliberately not composed into the active runtime.

Sprint 13 baseline: **130 passed, 1 warning in 1.30s**. Container now composes
an empty scoped repository; public requests still supply no scope and perform
no retrieval.

Sprint 14 baseline: **154 passed, 1 warning in 1.26s**. Prompt memory defaults
off and remains unreachable from the unscoped public route.

Sprint 15 baseline: **192 passed, 1 warning in 2.33s**. The functional demo
adds an explicit local comparison; the unscoped public route remains
unchanged.

Sprint 16 baseline: **221 passed, 1 warning in 1.47s**. Explicit update remains
disabled by default and absent from the public route.

Sprint 17 adds opt-in evidence-bounded response parsing and auditable selected
record numbers. It defaults off; absent or empty memory preserves the exact
historical path. The protocol validates structure and references, not truth or
semantic support, and the public route still supplies no scope.

## Integration limit and undecided items

The local resolver is not called by `CognitiveEngine.process`, the public API,
natural-language intent extraction, or an automatic resolve-or-reason
orchestrator. Default repositories are ephemeral; explicit operations
composition can inject SQLite durability. Identity authentication, integration
policy, encryption, synchronization, retention, semantic retrieval, truth
validation, and external-access governance remain deferred.

`app/brain/Brain` and `app/brain/Orchestrator` remain present but have no
consumer in the public cognitive route. Other historical modules under
`app/reasoning`, `app/context`, and `app/memory` remain outside this sprint.

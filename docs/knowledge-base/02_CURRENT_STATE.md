# Current State

Snapshot updated: **2026-07-30** (America/Tegucigalpa).

## Repository checkpoint

- Branch: `docs/engineering-platform`
- Commit: `74637ab126c6dc2942bb5ae01cea0f9db7cd1d30`
- Tag: `sprint-3-complete`
- Upstream: `origin/docs/engineering-platform`
- Working tree before this recovery pack: clean
- Working tree after generation: intentionally contains only the uncommitted
  documentation and backup-script changes listed by `git status`

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
| 4 | Completed in working tree | Public cognitive input now calls the Container-composed `CognitiveEngine` directly; behavioral API tests verify the boundary. |
| 5 | Completed in working tree | Capability Runtime v1 resolves and executes a registered deterministic capability and exposes its output. |
| 6 | Completed in working tree | Provider-backed `ReasoningCapability` is registered and executable on demand without changing the default public policy. |
| 7 | Completed in working tree | Ollama URL, model, and timeout now come from official validated application settings and are injected by `Container`. |
| 8 | Completed in working tree | An explicit deterministic policy selects `normalized_input` or `reasoning` solely from `REASONING_ENABLED`. |
| 9 | Completed in working tree | Active components, contracts, dependency rules, and minimal architecture enforcement now describe and protect the executable Core. |
| 10 | Completed in working tree | Structured cognitive outcomes distinguish success and controlled failure; the HTTP boundary maps stable codes safely. |
| 11 | Completed in working tree | Explicit Ollama readiness and a controlled opt-in reasoning demo were added outside the Core and public API. |
| 12 | Completed in working tree | A parallel read-only memory repository foundation enforces explicit scope ownership and A/B isolation without runtime integration. |
| 13 | Completed in working tree | Optional scoped retrieval enriches CognitiveContext before classification only when enabled and explicitly scoped. |
| 14 | Completed in working tree | A bounded prompt policy includes scoped memory as untrusted reference data while preserving the exact default prompt. |
| 15 | Completed in working tree | A local CLI compares baseline and scoped-memory reasoning with one readiness check, ephemeral records, and a safe immutable report. |

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
| Architecture tests | Integrated | Five import-boundary tests and two documentation-baseline tests inspect an explicit active-file scope using the standard library. |
| `CognitiveOutcome` / `CognitiveError` | Integrated | Enforce valid success/failure states and stable provider-independent errors. |
| `ResponseStage` | Integrated structured boundary | Returns real output as success or a structured controlled failure; it knows no HTTP. |
| Cognitive memory pipeline | Implemented and composed | Built in `Container`, exposed through a legacy adapter, but absent from the integrated request cycle. |
| `Capability` contract | Implemented contract only | No concrete capability integration found. |
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

## Next logical work and undecided items

Sprint 10 completes the structured success/failure and safe HTTP representation
scope. Operational availability, provider selection, memory, evidence, files,
web, legacy retirement, and richer evidence-bearing content remain deferred.

`app/brain/Brain` and `app/brain/Orchestrator` remain present but have no
consumer in the public cognitive route. Other historical modules under
`app/reasoning`, `app/context`, and `app/memory` remain outside this sprint.

# Current State

Snapshot generated: **2026-07-29** (America/Tegucigalpa).

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
| `ResponseStage` | Integrated with execution output | Returns usable capability output on success and safe fixed text on failure. |
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

Sprint 5 final result: **24 passed, 1 warning in 0.85s**. The warning remains a
`PytestCacheWarning` because pytest cannot create its cache node-id path. The
configured suite covers the registry, executor policy, deterministic
capability, engine handoff, and public route. Tests under `app/tests/` remain
excluded by `testpaths = ["tests"]`.

## Next logical work and undecided items

Sprint 5 establishes Capability Runtime v1. Candidate later topics include
memory, useful concrete capabilities, reasoning, files, and web. Unresolved
decisions include how memory joins the lifecycle, how richer responses represent
evidence, and how/when legacy modules are retired.

`app/brain/Brain` and `app/brain/Orchestrator` remain present but have no
consumer in the public cognitive route. Other historical modules under
`app/reasoning`, `app/context`, and `app/memory` remain outside this sprint.

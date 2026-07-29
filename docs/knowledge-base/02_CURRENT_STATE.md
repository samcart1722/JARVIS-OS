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
| 4 | Not started / not approved | Candidate scope only; no formal decision found. |

## Executable components and status

| Component | Classification | Evidence |
|---|---|---|
| `CognitiveEngine.process` | Integrated | Constructs `Goal`/`CognitiveContext`, classifies, routes, plans, executes, and formats. |
| `Container` | Integrated, partially scaffolded | Builds memory and cognitive engine; several `_build_*` methods are `pass`. |
| `DefaultGoalClassifier` | Provisional | Always returns `Domain.UNKNOWN`. |
| `SpecialistRouter` | Provisional | Maps every domain to one `DefaultSpecialist`. |
| `DefaultSpecialist` | Provisional | Creates one descriptive plan step. |
| `CapabilityExecutor` | Provisional | Traverses descriptions; invokes no `Capability`. |
| `ResponseStage` | Provisional | Returns one of two fixed strings. |
| Cognitive memory pipeline | Implemented and composed | Built in `Container`, exposed through a legacy adapter, but absent from the integrated request cycle. |
| `Capability` contract | Implemented contract only | No concrete capability integration found. |
| `InputStage` / `ContextStage` / `ReasoningStage` | Implemented separately | Not called by the Sprint 3 `CognitiveEngine.process` path. |

## Real request flow

The FastAPI `/brain/think` route constructs legacy `Brain`, which delegates to
legacy `Orchestrator`, then to `container.cognitive_engine.process`. The engine
runs:

`user_input → Goal + CognitiveContext → Domain → Specialist → Plan → ExecutionResult → ResponseStage → str`

See [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md) for exact boundaries.

## Tests

Command: `.\.venv\Scripts\python.exe -m pytest`

Result on 2026-07-29: **9 passed, 1 warning in 0.36s**. The sole warning was
`PytestCacheWarning` because pytest could not create its cache node-id path.
The configured suite covers eight `UserRequest` cases and one integrated engine
interaction. Tests under `app/tests/` are not collected by `testpaths = ["tests"]`.

## Next logical work and undecided items

The next logical activity is to define Sprint 4 through the project's
architecture process, not to assume its scope. Candidate topics include memory,
reasoning as a capability, files, web, and actual capability orchestration.
Unresolved decisions include which candidate comes first, how execution receives
context, how memory joins the lifecycle, and how/when legacy routes are retired.

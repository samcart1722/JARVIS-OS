# Sprint 9 Summary — Cognitive Core Governance Baseline v1

## Implemented

Completed the previously empty active-runtime documents:

- `docs/architecture/domains/Cognitive_Core/Components.md`;
- `docs/architecture/domains/Cognitive_Core/Contracts.md`;
- `docs/architecture/domains/Cognitive_Core/Dependency_Rules.md`.

They distinguish the Cognitive Core, Composition Root, Settings,
infrastructure, HTTP boundary, legacy modules, provisional behavior, and known
debt. They describe executable behavior only; Task Builder, evidence, memory
update, tools, provider availability, and other future lifecycle elements are
not presented as active.

## Enforcement

Added five AST-based import-boundary tests for an explicit active scope:

- reasoning selection contract and deterministic implementation;
- `DefaultSpecialist`;
- `CapabilityExecutor`;
- public `/brain/think` route;
- files directly under `app/cognition/domain`.

Added two documentation tests requiring the three files to exist, be non-empty,
contain essential sections, mention the active flow, and distinguish
infrastructure/legacy. Tests use only `ast` and `pathlib` from the standard
library. No generic static-analysis framework or dependency was added.

Historical `app/brain`, `app/reasoning`, `app/context`, `app/memory`, handlers,
prompt managers, and `app/tests` are explicitly excluded from active-Core
enforcement.

## Audit findings

No prohibited active-runtime imports were found. The documented allowed
boundary `ReasoningCapability -> ReasoningStage -> ReasoningProvider` keeps
`OllamaProvider` and `OllamaClient` outside the Core. Cognitive memory is
composed separately but remains absent from `CognitiveEngine.process`.
Classification, routing, planning, response richness, and several lifecycle
stages remain provisional or incomplete.

## Verification

Baseline: **63 passed, 1 warning in 0.87s**; Ruff passed and
`git diff --check` was clean.

Final: **70 passed, 1 warning in 1.10s** with `DEBUG=true`. Ruff passed. The
warning is the pre-existing pytest cache-path issue.

No production file, dependency, HTTP contract, runtime behavior, environment
file, or normative product/lifecycle document was changed.

No staging, commit, push, tag, or merge action was performed.

# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

Sprint 31 — Durable Action Permission Foundation v1 is the latest governed
implementation release.

Feature commit:
`0796cb54ee1d570852a85722af43b1b41a3b4881`

PR #40 merged through ordinary two-parent merge commit:
`9cad78ed22f0a6aef26eda0623d0f544cf65e5be`

Release tree:
`5ad6dc854c546e82cdab6c6fd5a5c48072b7fc0d`

Immutable governed annotated tag:
`governed-sprint-31-complete`

Annotated tag object:
`2f52c2973bd349bd4302d7bb1e59307f5b14708c`

The tag peels to the release commit above.

Post-merge validation passed 117 architecture tests and 1,119 repository
tests. Ruff and `git diff --check` passed.

The authoritative recoverable backup is:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260821_095503`

Bundle recovery reproduced the exact release commit, governed tag object,
tag peel, release tree, `master`, and a clean worktree.

Sprint 31 makes exact actor/workspace/action permission durability available
through explicit repository injection while preserving authentication,
principal-to-actor mapping, workspace selection, membership admission, and
action authorization as separate boundaries. Membership alone does not grant
an action. Missing or known repository-failure permission state denies access.

Default `Container` composition remains no-I/O. Sprint 31 adds no public
authentication transport, roles/RBAC, wildcard or inherited permissions,
grant/revoke API, session/device lifecycle, credential persistence, or public
HTTP exposure.

Independent review was unavailable for Sprint 31 and no independent review is
claimed. Same-assistant technical and adversarial reviews were performed and
identified and corrected a schema-verification defect before release.

Sprint 31 implementation and release-truth integration are complete.
Documentation synchronization commit `d79552f9ab19d7b2da9f2a60be4ef48b8b9608cd`
merged through PR #41 at canonical merge
`7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`. Canonical validation passed 117
architecture and 1,119 repository tests, Ruff, and `git diff --check`. The
merged implementation and release-truth branches were cleaned locally and
remotely. The current `chore/sprint-31-closure-truth-finalization` branch remains
for this bounded final correction; its governed integration and formal Sprint
31 closure are still pending. No subsequent implementation sprint is
authorized by this checkpoint.

Sprint 25 is completed through merged PR #24 at
`1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`
(annotated tag object `6e0de87b426e4a7d4c3103bdffc77f2b171aa30f`). It adds
strict JSON `knowledge read` / `knowledge store` commands to the existing
interpreter and text router. This is deterministic structured-command parsing,
not general natural-language understanding. Malformed commands in the
`knowledge` namespace are terminal; public HTTP remains unchanged.
Release validation passed 680 tests, including 85 focused tests. Sprint 26 was
subsequently implemented and merged as described above.

Sprint 23's explicit application coordinator tries an already-typed local
intent first. Handled local success or failure is terminal; only
`not_handled`, explicit fallback authorization, and valid cognitive input can
select the existing cognitive path.

The coordinator is not used by public HTTP and performs no natural-language
parsing. Default `Container` construction remains in-memory and inert.

- The current runtime extends the released Sprint 22 durable local foundation
  with explicit, caller-authorized routing coordination.
- The latest immutable governed implementation release tag is
  `governed-sprint-31-complete`; its annotated tag object is
  `2f52c2973bd349bd4302d7bb1e59307f5b14708c` and it peels to
  `9cad78ed22f0a6aef26eda0623d0f544cf65e5be`.
- The public HTTP path remains the historical `CognitiveEngine` route: input
  becomes a `Goal` and `CognitiveContext`, is classified,
  routed to a specialist, converted to a `Plan`, traversed by
  `CapabilityExecutor`, and formatted by `ResponseStage`.
- Sprint 21 separately provides a typed, authorized, deterministic local list
  path with zero model calls. It is not exposed through public HTTP and there
  is no automatic natural-language routing or resolve-or-reason bridge.
  Classification within the historical path still falls back
  to `Domain.UNKNOWN`. The public `CognitiveEngine` path uses
  `CapabilityExecutor` and registered concrete capabilities; its default policy
  selects `NormalizedInputCapability` unless reasoning is explicitly enabled.
  Public HTTP supplies no explicit scope and therefore does not use the
  separate Sprint 21 local resolver.

## Essential guardrails

The model is not the Core. The Core remains domain-independent. Specialists
plan; reusable capabilities perform work; the `CognitiveEngine` orchestrates;
the `Container` composes dependencies. Runtime and architecture documentation
must remain aligned. Record material architectural changes through an ADR.

Do not change architecture before reviewing the Product North Star, Cognitive
Lifecycle, and applicable ADRs. At this checkpoint no ADR records directory or
approved ADR was found; do not treat draft standards or RFCs as decisions.

## Required reading order

1. [Canonical Project State](LUXIOM_CANONICAL_PROJECT_STATE.md)
2. [Product North Star](docs/00_Product_North_Star.md)
3. [Cognitive Lifecycle](docs/01_Cognitive_Lifecycle.md)
4. [Local-First Knowledge and Model Policy](docs/02_Local_First_Knowledge_and_Model_Policy.md)
5. [Knowledge Base index](docs/knowledge-base/00_INDEX.md)
6. [Current State](docs/knowledge-base/02_CURRENT_STATE.md)
7. [Runtime Architecture](docs/knowledge-base/03_RUNTIME_ARCHITECTURE.md)
8. [Decisions and Guardrails](docs/knowledge-base/04_DECISIONS_AND_GUARDRAILS.md)
9. [Technical Debt](docs/knowledge-base/05_TECHNICAL_DEBT.md)
10. [AI Handoff](docs/knowledge-base/07_AI_HANDOFF.md)

The complete recovery documentation lives in
[`docs/knowledge-base/`](docs/knowledge-base/00_INDEX.md).

## Minimum verified commands

Run from the repository root in Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest
git status --short --branch
git log --oneline --decorate -10
```

The project metadata requires Python 3.12 or newer and declares development
dependencies in `pyproject.toml`. If the existing virtual environment is
unavailable, create and install one explicitly:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

Sprint 28 Durable Actor–Workspace Membership Foundation v1 is the latest
immutable implementation release. Feature commit
`95341198145f84d80c7cf37bf73b707cfe574a21` merged through PR #32 as normal
two-parent merge commit `be22ffddda6d6961497c338caadf4c85e0fcb3ed`.
The annotated tag `sprint-28-complete` points to that commit; its tag object is
`986ae13ca8fefcbd6197db8a723e25ae4e3dc62a`. Validation passed 915 repository,
78 architecture, and 156 focused tests, Ruff, and both demos. The independently
recovered backup is `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260817_190455`.
The full release record is the
[Sprint 28 summary](docs/knowledge-base/history/sprints/SPRINT_28_SUMMARY.md).
Sprint 29 has not been authorized and must not begin until Sprint 28
release-governance closure is complete.

Membership is workspace admission, not authentication or action authorization.
Identities are typed values, not proof; trusted binding is not durable
membership; `PermissionPolicy` remains downstream. Default `Container` remains
in-memory/no-I/O, and no public membership/authentication transport was added.
Sprint 27 remains the prior completed tagged capability release.

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
- The latest immutable implementation release tag is `sprint-28-complete`; its
  tag object is `986ae13ca8fefcbd6197db8a723e25ae4e3dc62a` and it peels to
  `be22ffddda6d6961497c338caadf4c85e0fcb3ed`.
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

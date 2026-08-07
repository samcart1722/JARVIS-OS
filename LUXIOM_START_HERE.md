# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

Sprint 27 Trusted Request Context Foundation v1 is fully released. Its feature
commit is
`feb5405d9c0dae123c366dc4ce405fb9e9f2a30a`, its functional merge is
`758e63278f0b342302dd1ed0d41f8514d1d9f1c3`, and release-truth governance
merged through PR #30 at `1501183b4c40faaba278f8d61f875d65954223a7`.
The annotated tag `sprint-27-complete` points to that release commit; its tag
object is `35a198af85299e9e09d086e63f66020ccdc522d3`. Final validation passed 117
focused, 70 architecture, and 836 repository tests, Ruff, and the 7/7 demo. The
verified release backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260807_160935`.

Sprint 27 is the latest completed tagged release. Its internal trusted-host
boundary is not authentication: the binding selector is not identity proof,
`PermissionPolicy` remains downstream, and public HTTP does not use the
boundary. Sprint 26 remains the prior completed tagged release at
`sprint-26-complete`.

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
- The latest completed release tag is `sprint-27-complete`; its annotated tag
  object is `35a198af85299e9e09d086e63f66020ccdc522d3` and it peels to
  `1501183b4c40faaba278f8d61f875d65954223a7`.
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

1. [Product North Star](docs/00_Product_North_Star.md)
2. [Cognitive Lifecycle](docs/01_Cognitive_Lifecycle.md)
3. [Local-First Knowledge and Model Policy](docs/02_Local_First_Knowledge_and_Model_Policy.md)
4. [Knowledge Base index](docs/knowledge-base/00_INDEX.md)
5. [Current State](docs/knowledge-base/02_CURRENT_STATE.md)
6. [Runtime Architecture](docs/knowledge-base/03_RUNTIME_ARCHITECTURE.md)
7. [Decisions and Guardrails](docs/knowledge-base/04_DECISIONS_AND_GUARDRAILS.md)
8. [Technical Debt](docs/knowledge-base/05_TECHNICAL_DEBT.md)
9. [AI Handoff](docs/knowledge-base/07_AI_HANDOFF.md)

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

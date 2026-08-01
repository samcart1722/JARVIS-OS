# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

Sprint 22 is implemented in `feat/sprint-22-durable-local-knowledge` and remains
pending commit, PR, merge, and tag. Its explicitly composed SQLite path persists
typed lists and immutable knowledge records across processes. The Core depends
only on repository contracts; default `Container` construction remains in-memory
and creates no database. It adds no public HTTP exposure, natural-language
routing, or automatic resolve-or-reason bridge.

- The current runtime extends the released **Sprint 21 local-first resolution
  foundation** with uncommitted Sprint 22 durability.
- The canonical released baseline before this branch is `sprint-21-complete` at
  `8c0330b54fca07eb2fe03657f499bc7fbac9e898`.
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

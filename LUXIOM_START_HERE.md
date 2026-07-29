# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

- Last completed sprint: **Sprint 3 — Cognitive Core integration**
  (`74637ab`, tag `sprint-3-complete`).
- Verified runtime: input becomes a `Goal` and `CognitiveContext`, is classified,
  routed to a specialist, converted to a `Plan`, traversed by
  `CapabilityExecutor`, and formatted by `ResponseStage`.
- Current behavior is deliberately minimal: classification always falls back
  to `Domain.UNKNOWN`; the default specialist creates one descriptive step;
  the executor invokes no concrete capability; memory is not in this cycle.
- Next work: define Sprint 4 formally. Candidate areas are documented, but
  Sprint 4 is not approved or started.

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
3. [Knowledge Base index](docs/knowledge-base/00_INDEX.md)
4. [Current State](docs/knowledge-base/02_CURRENT_STATE.md)
5. [Runtime Architecture](docs/knowledge-base/03_RUNTIME_ARCHITECTURE.md)
6. [Decisions and Guardrails](docs/knowledge-base/04_DECISIONS_AND_GUARDRAILS.md)
7. [Technical Debt](docs/knowledge-base/05_TECHNICAL_DEBT.md)
8. [AI Handoff](docs/knowledge-base/07_AI_HANDOFF.md)

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

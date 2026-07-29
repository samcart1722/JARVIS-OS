# AI Handoff

## Recovery brief

1. **Identity:** Luxiom is a domain-independent Cognitive Operating System, not
   a chatbot, LLM wrapper, conventional agent, or single-industry product.
   HealthBridge is its first planned consumer, not part of the Core.
2. **Exact checkpoint:** branch `docs/engineering-platform`, commit
   `74637ab126c6dc2942bb5ae01cea0f9db7cd1d30`, tag
   `sprint-3-complete`, as verified on 2026-07-29.
3. **Runtime:** `Brain → Orchestrator → CognitiveEngine → Goal/CognitiveContext
   → classifier → specialist → Plan → CapabilityExecutor → ExecutionResult
   → ResponseStage`.
4. **Important components:** `app/cognition/engine.py`,
   `app/core/container.py`, classification, specialists, planning,
   capabilities, response stage, and the separately composed cognitive memory
   pipeline.
5. **Completed work:** Sprints 0–3 are tagged and summarized under
   [`history/sprints/`](history/sprints/SPRINT_0_SUMMARY.md).
6. **Non-negotiable guardrails:** models are providers, Core is
   domain-independent, specialists plan, capabilities are reusable,
   `CognitiveEngine` orchestrates, and `Container` composes dependencies.
7. **Known debt:** executor lacks context; classification/default planning and
   response are minimal; no concrete capability executes; memory is outside the
   active cycle; legacy paths and identity inconsistencies remain; configured
   tests exclude `app/tests`.
8. **Changes requiring architectural review:** Core/domain coupling, lifecycle
   changes, collaborator responsibilities, executor/capability contracts,
   memory ownership, legacy removal, product-specific exceptions, or replacing
   provider independence.
9. **Reading order:** Product North Star → Cognitive Lifecycle →
   [Knowledge Base index](00_INDEX.md) → Current State → Runtime Architecture →
   Decisions/Guardrails → Technical Debt → Roadmap.
10. **Validation:** inspect `git status`, branch, HEAD, tags, recent log, runtime
    code and test configuration; then run the configured pytest suite. Do not
    rely on this snapshot if the repository has moved.
11. **Recommended next step:** formally define Sprint 4. Candidate scope exists,
    but no approval was found and no implementation should be assumed.
12. **Do not assume:** that draft architecture is approved; that interfaces are
    integrated features; that all repository tests are collected; that the
    Ollama reasoning stage is active; that memory updates occur; that
    HealthBridge belongs in Core; or that JARVIS naming means the product is not
    Luxiom.

## Questions to answer from code before proposing changes

- What commit, branch, tags, and working-tree changes now exist?
- Which API/CLI entry point actually reaches `CognitiveEngine`?
- Which stages are constructed and which are called at runtime?
- Does the executor receive enough context for the `Capability` contract?
- Which concrete capabilities are registered and invoked?
- Where is memory composed, and does the request lifecycle call it?
- Which tests does `pyproject.toml` collect, and what is excluded?
- Which legacy modules are still imported by active paths?
- What normative documents are approved versus Draft?
- Is there now an ADR directory or a formal Sprint 4 decision?
- Have identity/configuration strings been deliberately migrated?

## Copy-Paste Recovery Prompt

```text
You are taking over the Luxiom repository without access to previous chats.
Treat the repository and Git history as the primary evidence.

First read LUXIOM_START_HERE.md. Then read docs/00_Product_North_Star.md,
docs/01_Cognitive_Lifecycle.md, and every document linked from
docs/knowledge-base/00_INDEX.md. Review foundation and architecture documents,
preserving their status (Approved, Draft, RFC, etc.), and inspect any ADRs.

Before proposing or changing anything:
1. Run git status, identify branch/HEAD/tags, and inspect recent history.
2. Inspect the executable Cognitive Core, Container, public entry points, test
   configuration, and legacy imports.
3. Run the configured tests and report the exact result.
4. Compare documented architecture with the runtime and record discrepancies.

Do not redesign the architecture, rebrand the project, resolve technical debt,
or treat a scaffold/interface as completed functionality without explicit
scope and architectural review. Models are replaceable providers, not the
Core; the Core remains domain-independent; specialists plan; capabilities are
reusable; CognitiveEngine orchestrates; Container is the Composition Root.

Confirm the current state before continuing. Resume from the latest sprint that
Git and tests confirm. At the recovery-pack checkpoint this was Sprint 3 at
74637ab (tag sprint-3-complete), while Sprint 4 was not approved or started;
verify that this remains true rather than assuming it.
```

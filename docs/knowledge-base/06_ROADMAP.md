# Roadmap

## Completed sprints

| Sprint | Objective achieved | Evidence |
|---|---|---|
| 0 | Recover a stable cognitive entry point and preserve compatibility with legacy memory. | `daa3698`, tag `sprint-0-complete` |
| 1 | Establish the minimal cognitive pipeline and a replaceable reasoning provider boundary. | `eca10d4`, `8404219`, tag `sprint-1-complete` |
| 2 | Define fundamental Cognitive Core domain/contracts and normative product/lifecycle documents. | `a53c1df`, tag `sprint-2-complete` |
| 3 | Wire the goal-classifier/specialist/plan/executor/response path into the engine and Container, with an integration test. | `74637ab`, tag `sprint-3-complete` |
| 4 | Make the Container-composed `CognitiveEngine` the sole public cognitive runtime and disconnect the legacy HTTP bridge. | Working-tree implementation and `history/sprints/SPRINT_4_SUMMARY.md` |
| 5 | Establish Capability Runtime v1 with logical identifiers, direct registry, fail-fast execution, and deterministic public output. | Working-tree implementation and `history/sprints/SPRINT_5_SUMMARY.md` |
| 6 | Register provider-backed reasoning as an opt-in capability while preserving deterministic public behavior. | Working-tree implementation and `history/sprints/SPRINT_6_SUMMARY.md` |
| 7 | Externalize Ollama URL, model, and timeout through official Settings and explicit composition. | Working-tree implementation and `history/sprints/SPRINT_7_SUMMARY.md` |
| 8 | Add an explicit deterministic policy selecting normalized input or reasoning from operational enablement. | Working-tree implementation and `history/sprints/SPRINT_8_SUMMARY.md` |

Detailed evidence is in [`history/sprints/`](history/sprints/SPRINT_0_SUMMARY.md).

## Current state

Sprint 8 is complete in the working tree. `Container` translates
`REASONING_ENABLED` into an injected selection policy. The safe default remains
`false`, so the public route selects `normalized_input` and does not require
Ollama. Explicit `true` selects `reasoning` without heuristics or fallback.

## Candidate scope after Sprint 8

The following remain candidates, not commitments:

- integrate Memory into the lifecycle;
- define provider availability and operational failure policy;
- add a Files capability;
- add a Web capability;
- add capabilities that perform useful work through separately approved scope.

Before selecting scope, resolve the executor/context contract, determine which
existing pipeline abstractions remain valid, define test boundaries, and record
any material architectural decision through the appropriate governance process.

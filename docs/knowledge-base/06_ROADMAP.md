# Roadmap

## Completed sprints

| Sprint | Objective achieved | Evidence |
|---|---|---|
| 0 | Recover a stable cognitive entry point and preserve compatibility with legacy memory. | `daa3698`, tag `sprint-0-complete` |
| 1 | Establish the minimal cognitive pipeline and a replaceable reasoning provider boundary. | `eca10d4`, `8404219`, tag `sprint-1-complete` |
| 2 | Define fundamental Cognitive Core domain/contracts and normative product/lifecycle documents. | `a53c1df`, tag `sprint-2-complete` |
| 3 | Wire the goal-classifier/specialist/plan/executor/response path into the engine and Container, with an integration test. | `74637ab`, tag `sprint-3-complete` |
| 4 | Make the Container-composed `CognitiveEngine` the sole public cognitive runtime and disconnect the legacy HTTP bridge. | Working-tree implementation and `history/sprints/SPRINT_4_SUMMARY.md` |

Detailed evidence is in [`history/sprints/`](history/sprints/SPRINT_0_SUMMARY.md).

## Current state

Sprint 4 is complete in the working tree. `POST /brain/think` now calls the
Container-composed `CognitiveEngine` directly and returns the result of
`ResponseStage`. The structure executes end to end through `ResponseStage`,
but classifier, specialist, plan, executor, and response behavior remain
minimal. No concrete capability and no memory update participate in that cycle.

## Candidate scope after Sprint 4

The following remain candidates, not commitments:

- integrate Memory into the lifecycle;
- model Reasoning as a reusable capability;
- add a Files capability;
- add a Web capability;
- implement actual capability registration/orchestration.

Before selecting scope, resolve the executor/context contract, determine which
existing pipeline abstractions remain valid, define test boundaries, and record
any material architectural decision through the appropriate governance process.

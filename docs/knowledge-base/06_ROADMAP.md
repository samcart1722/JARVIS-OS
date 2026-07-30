# Roadmap

## Sprint 11 completed

Provider Readiness and Demo Runtime v1 adds an explicit non-generative Ollama
check, safe operational states, inert composition, and an opt-in CLI demo
gated by `REASONING_ENABLED`. It adds no endpoint, automatic check, retry,
fallback, model lifecycle operation, or public API change.

## Sprint 12 completed

Scoped Memory Persistence Foundation v1 establishes explicit ownership,
repository-boundary filtering, deterministic literal search, immutable
results, and tested isolation. Sprint 13 may integrate controlled read-only
retrieval while preserving these invariants. Migration, writes, durable
persistence, and prompt incorporation remain deferred.

## Sprint 13 completed

Controlled Memory Context Integration v1 composes the empty scoped repository,
adds an opt-in flag, retrieves only with explicit scope, and propagates an
immutable snapshot before classification. Public HTTP and demo behavior remain
unchanged. Real scoped data sources, identity, writes, durability, migration,
and safe prompt use remain future work.

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
| 9 | Complete active Cognitive Core documentation and enforce confirmed boundaries with standard-library architecture tests. | Working-tree implementation and `history/sprints/SPRINT_9_SUMMARY.md` |
| 10 | Introduce structured cognitive outcomes and safe HTTP success/failure mapping. | Working-tree implementation and `history/sprints/SPRINT_10_SUMMARY.md` |

Detailed evidence is in [`history/sprints/`](history/sprints/SPRINT_0_SUMMARY.md).

## Current state

Sprint 10 is complete in the working tree. The Core returns a validated
`CognitiveOutcome`; controlled failures carry stable codes and are mapped by
the API to safe HTTP 500/503 responses. The successful deterministic and
reasoning paths retain their prior output.

## Candidate scope after Sprint 10

The following remain candidates, not commitments:

- integrate Memory into the lifecycle;
- define provider availability and operational failure policy;
- add a Files capability;
- add a Web capability;
- add capabilities that perform useful work through separately approved scope.

Before selecting scope, resolve the executor/context contract, determine which
existing pipeline abstractions remain valid, define test boundaries, and record
any material architectural decision through the appropriate governance process.

## Sprint 14 completed

Memory-Aware Reasoning Prompt Policy v1 adds exact default compatibility,
bounded scoped-reference inclusion, stable safety instructions, and provider
injection. Public behavior remains unchanged. Advanced injection defense,
ranking, durable memory, writes, migration, identity, and token limits remain
future work.

## Sprint 15 completed

Functional Cognitive Demo v1 provides a controlled local baseline versus
memory-aware comparison with one readiness check, explicit ephemeral scope,
isolated flags, visible outcomes, and no persistence or fallback. Public API
behavior remains unchanged.

## Sprint 16 completed

Explicit Scoped Memory Update v1 adds a separate writer contract, ordered
ephemeral append, opt-in update service, shared reader/writer repository, and a
controlled before/update/after CLI. It adds no automatic extraction,
persistence, legacy migration, or HTTP behavior.

## Sprint 17 completed

Evidence-Bounded Memory Reasoning v1 adds an independent opt-in flag, shared
bounded evidence selection, strict JSON envelope parsing, auditable record
references, deterministic insufficient-evidence output, controlled protocol
failure, and a comparative local demo. It does not verify truth, semantically
fact-check claims, retry, repair JSON, fall back to free text, persist memory,
or change the HTTP surface.

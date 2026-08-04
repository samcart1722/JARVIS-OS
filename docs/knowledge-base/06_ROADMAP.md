# Roadmap

Sprint 24 is released at `fe958f45409c0fc11df38cd945ae9678e3ad9e23`,
tag `sprint-24-complete`. Sprint 25 adds only strict deterministic JSON
knowledge commands in its feature working tree pending release. Broader
language interpretation and public exposure remain unapproved and deferred.

Sprint 24 released deterministic local command interpretation at merge
`fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`.
Broad natural language, public exposure, authentication and RBAC, semantic
retrieval, knowledge prompts, synchronization, encryption, retention, and
external access remain unapproved deferrals. The Constitution and ADR standard
remain Draft; no approved ADR is implied.

With Sprint 25 implemented in the feature working tree, vendor/family diversity
policy, truth checking, external
sources, deterministic entailment, confidence, contradictions, partial
filtering, durable audit, HTTP exposure, and human review remain deferred.

Model-assisted support classification is complete. Factual truth, deterministic
entailment, guaranteed epistemic independence, contradictions, claim atomicity,
calibrated confidence, broader knowledge persistence, identity, HTTP, and
ranking remain open.

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
| 11 | Add explicit provider readiness and an opt-in operational demo. | `4428a2a`, tag `sprint-11-complete` |
| 12 | Establish scoped, isolated in-memory persistence contracts. | `0264300`, tag `sprint-12-complete` |
| 13 | Integrate optional scoped memory context retrieval. | `372c4cc`, tag `sprint-13-complete` |
| 14 | Add bounded memory-aware reasoning prompt policy. | `1b29dc8`, tag `sprint-14-complete` |
| 15 | Add the controlled functional cognitive comparison demo. | `183ef47`, tag `sprint-15-complete` |
| 16 | Add explicit opt-in scoped memory updates. | `ac45d39`, tag `sprint-16-complete` |
| 17 | Add evidence-bounded memory reasoning. | `825b1da`, tag `sprint-17-complete` |
| 18 | Add claim-level evidence attribution. | `7823429`, tag `sprint-18-complete` |
| 19 | Add model-assisted claim support verification. | `32c9319`, tag `sprint-19-complete` |
| 20 | Add independent verifier-client composition. | `ca4fa2d`, tag `sprint-20-complete` |
| 21 | Add the typed local-first list foundation. | `8c0330b`, tag `sprint-21-complete` |
| 22 | Add durable local list and minimal knowledge persistence. | `9dcb36b`, tag `sprint-22-complete` |
| 23 | Add explicit local-first cognitive routing coordination. | `be59175c`, tag `sprint-23-complete` |
| 24 | Add bounded deterministic list-command interpretation and explicit text routing. | `fe958f45`, tag `sprint-24-complete` |
| 25 | Add strict deterministic local knowledge commands. | Implemented in feature working tree; pending release |

Detailed evidence is in [`history/sprints/`](history/sprints/SPRINT_0_SUMMARY.md).

## Current state

Sprint 25 is implemented but uncommitted in the feature working tree. The
typed resolver remains separate from the public HTTP/CognitiveEngine path. The
Core preserves validated
`CognitiveOutcome`; controlled failures carry stable codes and are mapped by
the API to safe HTTP 500/503 responses. The successful deterministic and
reasoning paths retain their prior output.

## Candidate scope after Sprint 25

The following remain candidates, not commitments:

- define authenticated identity, retention, encryption and synchronization;
- define semantic retrieval and truth-validation policy separately;
- define authentication and any future public coordinator integration;
- define migration, audit, synchronization, and external-access policy before
  adding durable or connected behavior.

These are deferred candidates, not Sprint 25 scope. Before selecting work,
define test boundaries and record material decisions through the appropriate
governance process.

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

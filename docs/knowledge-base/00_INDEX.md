# Luxiom Knowledge Base

This directory is an operational map and recovery aid. It summarizes and links
to authoritative material; it does not replace normative documents.

## Recommended reading order

Sprint 38 Authorized local knowledge browse v1 is the latest implementation
release at `97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4`, annotated tag
`governed-sprint-38-complete`.
Sprint 38 is CLOSED. Its Authorized local knowledge browse v1 implementation
was released through merged PR #58 and immutable tag
`governed-sprint-38-complete`. Documentation PR #59 and the final closure PR
#60 are merged; their release truth is incorporated into `master` at
`a5c92f052cc2eb7294767c1f5514ee54bc4b61ca`. The verified backup and recovery
evidence is recorded at
`C:\\PROYECTOS\\LUXIOM_BACKUPS\\LUXIOM_20260911_191202_SPRINT38_CLOSURE`,
and prior Sprint 38 feature/documentation branches were cleaned locally and
remotely. Formal closure is complete, with no known open functional defects.
Sprint 39 is the active pre-merge implementation scope for
`Authorized Local Knowledge Browse Continuation v1`. Blocks A-E are approved;
Block F validation and documentation remain in progress. The scope is not yet
merged, released, closed or tagged.
Sprint 37 and earlier releases remain historical. Sprint 39 remains pre-merge
and has no final release closure yet.
Start with the repository-owned
[Canonical Project State](../../LUXIOM_CANONICAL_PROJECT_STATE.md), then see
the [Sprint 28 summary](history/sprints/SPRINT_28_SUMMARY.md) and
[Sprint 27 summary](history/sprints/SPRINT_27_SUMMARY.md).

1. [Project Context](01_PROJECT_CONTEXT.md) — identity, purpose, and platform model.
2. [Current State](02_CURRENT_STATE.md) — dated, evidence-based repository snapshot.
3. [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md) — what the code actually runs.
4. [Decisions and Guardrails](04_DECISIONS_AND_GUARDRAILS.md) — confirmed constraints and provenance.
5. [Technical Debt](05_TECHNICAL_DEBT.md) — verified gaps that remain unresolved.
6. [Roadmap](06_ROADMAP.md) — completed work and unapproved candidate next scope.
7. [AI Handoff](07_AI_HANDOFF.md) — context transfer and recovery prompt.
8. [Backup and Recovery](08_BACKUP_AND_RECOVERY.md) — portable backup procedure.
9. [Source of Truth](09_SOURCE_OF_TRUTH.md) — precedence and conflict resolution.

Before this sequence, read the normative
[Product North Star](../00_Product_North_Star.md) and
[Cognitive Lifecycle](../01_Cognitive_Lifecycle.md), followed by the
[Local-First Knowledge and Model Policy](../02_Local_First_Knowledge_and_Model_Policy.md).

## Document classes

| Class | Documents | Role |
|---|---|---|
| Normative / governing | [Product North Star](../00_Product_North_Star.md), [Cognitive Lifecycle](../01_Cognitive_Lifecycle.md), [Local-First Knowledge and Model Policy](../02_Local_First_Knowledge_and_Model_Policy.md), foundation and architecture documents linked from [Source of Truth](09_SOURCE_OF_TRUTH.md) | Define intended identity, lifecycle, and constraints; status labels still matter. |
| Operational state | [Current State](02_CURRENT_STATE.md), [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md), [Technical Debt](05_TECHNICAL_DEBT.md) | Describe verified executable reality at a point in time. |
| Planning | [Roadmap](06_ROADMAP.md) | Separates completed sprints from unapproved candidates. |
| History | [Sprint summaries](history/sprints/SPRINT_0_SUMMARY.md), [Sprint 20 summary](history/sprints/SPRINT_20_SUMMARY.md), [Sprint 21 summary](history/sprints/SPRINT_21_SUMMARY.md), [Sprint 22 summary](history/sprints/SPRINT_22_SUMMARY.md), [Sprint 23 summary](history/sprints/SPRINT_23_SUMMARY.md), [Sprint 24 summary](history/sprints/SPRINT_24_SUMMARY.md), [Sprint 25 summary](history/sprints/SPRINT_25_SUMMARY.md), [conversation policy](history/conversations/README.md) | Preserve traceable context without becoming normative truth. |
| Recovery | [Canonical Project State](../../LUXIOM_CANONICAL_PROJECT_STATE.md), [AI Handoff](07_AI_HANDOFF.md), [Backup and Recovery](08_BACKUP_AND_RECOVERY.md), [Source of Truth](09_SOURCE_OF_TRUTH.md) | Restore context, release evidence, repository history, and working practices. |

## Cognitive Core governance baseline

- [Active components](../architecture/domains/Cognitive_Core/Components.md)
- [Active contracts](../architecture/domains/Cognitive_Core/Contracts.md)
- [Dependency rules](../architecture/domains/Cognitive_Core/Dependency_Rules.md)

## Operations

- [Durable Actor-Workspace Membership Demo](../operations/DURABLE_ACTOR_WORKSPACE_MEMBERSHIP_DEMO.md)
  proves persistence and admission/permission separation.

- [Deterministic Local Knowledge Commands Demo](../operations/DETERMINISTIC_LOCAL_KNOWLEDGE_COMMANDS_DEMO.md)
  proves strict knowledge store/read routing and terminal local outcomes.

- [Deterministic Local Command Interpretation Demo](../operations/DETERMINISTIC_LOCAL_COMMAND_INTERPRETATION_DEMO.md)
  proves all five Sprint 24 routes with real in-memory composition.

- [Explicit Local-First Cognitive Routing Demo](../operations/LOCAL_FIRST_COGNITIVE_ROUTING_DEMO.md)
  shows terminal local handling, denied fallback, and explicitly authorized
  deterministic cognitive routing.

- [Durable Local Knowledge Demo](../operations/DURABLE_LOCAL_KNOWLEDGE_DEMO.md)
  runs explicit `seed` and `verify` processes against a caller-supplied database.

- [Durable Action Permission Revocation Demo](../operations/DURABLE_ACTION_PERMISSION_REVOCATION_DEMO.md)
  proves exact revocation durability through separate `revoke` and `verify`
  Python processes against the same external database.

- [Functional Cognitive Demo v1](../operations/FUNCTIONAL_COGNITIVE_DEMO.md)
- [Explicit Scoped Memory Update Demo v1](../operations/EXPLICIT_MEMORY_UPDATE_DEMO.md)
- [Claim-Level Evidence Attribution Demo v1](../operations/CLAIM_LEVEL_EVIDENCE_ATTRIBUTION_DEMO.md)
- [Claim Evidence Support Verification Demo v1](../operations/CLAIM_EVIDENCE_VERIFICATION_DEMO.md)
- [Independent Claim Verifier Demo v1](../operations/INDEPENDENT_CLAIM_VERIFIER_DEMO.md)
- [Local-First Family Resolution Demo v1](../operations/LOCAL_FIRST_FAMILY_RESOLUTION_DEMO.md)

## Sprint implementation history

- [Sprint 29 release summary](history/sprints/SPRINT_29_SUMMARY.md)
- [Sprint 28 release summary](history/sprints/SPRINT_28_SUMMARY.md)

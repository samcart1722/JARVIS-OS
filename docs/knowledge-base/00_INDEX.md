# Luxiom Knowledge Base

This directory is an operational map and recovery aid. It summarizes and links
to authoritative material; it does not replace normative documents.

## Recommended reading order

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
| History | [Sprint summaries](history/sprints/SPRINT_0_SUMMARY.md), [Sprint 20 summary](history/sprints/SPRINT_20_SUMMARY.md), [Sprint 21 summary](history/sprints/SPRINT_21_SUMMARY.md), [Sprint 22 summary](history/sprints/SPRINT_22_SUMMARY.md), [conversation policy](history/conversations/README.md) | Preserve traceable context without becoming normative truth. |
| Recovery | [AI Handoff](07_AI_HANDOFF.md), [Backup and Recovery](08_BACKUP_AND_RECOVERY.md), [Source of Truth](09_SOURCE_OF_TRUTH.md) | Restore context, repository history, and working practices. |

## Cognitive Core governance baseline

- [Active components](../architecture/domains/Cognitive_Core/Components.md)
- [Active contracts](../architecture/domains/Cognitive_Core/Contracts.md)
- [Dependency rules](../architecture/domains/Cognitive_Core/Dependency_Rules.md)

## Operations

- [Durable Local Knowledge Demo](../operations/DURABLE_LOCAL_KNOWLEDGE_DEMO.md)
  runs explicit `seed` and `verify` processes against a caller-supplied database.

- [Functional Cognitive Demo v1](../operations/FUNCTIONAL_COGNITIVE_DEMO.md)
- [Explicit Scoped Memory Update Demo v1](../operations/EXPLICIT_MEMORY_UPDATE_DEMO.md)
- [Claim-Level Evidence Attribution Demo v1](../operations/CLAIM_LEVEL_EVIDENCE_ATTRIBUTION_DEMO.md)
- [Claim Evidence Support Verification Demo v1](../operations/CLAIM_EVIDENCE_VERIFICATION_DEMO.md)
- [Independent Claim Verifier Demo v1](../operations/INDEPENDENT_CLAIM_VERIFIER_DEMO.md)
- [Local-First Family Resolution Demo v1](../operations/LOCAL_FIRST_FAMILY_RESOLUTION_DEMO.md)

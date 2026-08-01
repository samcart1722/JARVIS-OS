# Source of Truth

## Trust hierarchy

1. Approved Product North Star and normative foundation/lifecycle documents:
   - [`docs/00_Product_North_Star.md`](../00_Product_North_Star.md)
   - [`docs/01_Cognitive_Lifecycle.md`](../01_Cognitive_Lifecycle.md)
   - [`docs/02_Local_First_Knowledge_and_Model_Policy.md`](../02_Local_First_Knowledge_and_Model_Policy.md)
   - Foundation documents according to their individual status. The
     [Constitution](../foundation/CONSTITUTION.md) remains Draft.
2. Approved, current ADRs. **None were found at this checkpoint.** The file
   [`Architecture_Decision_Record_Standard.md`](../architecture/Architecture_Decision_Record_Standard.md)
   is a Draft standard, not an ADR decision.
3. Executable code and configured tests, principally `app/`, `tests/`,
   `pyproject.toml`, and `app/core/container.py`.
4. [Current State](02_CURRENT_STATE.md) and [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md).
5. Git history, signed/known remotes, and sprint tags.
6. [Roadmap](06_ROADMAP.md).
7. [Sprint summaries](history/sprints/SPRINT_0_SUMMARY.md).
8. Archived conversations and session summaries.

Document status is part of authority. Draft architecture files—including
[`Architectural_Invariants.md`](../architecture/Architectural_Invariants.md),
[`Luxiom_Architecture_Blueprint.md`](../architecture/Luxiom_Architecture_Blueprint.md),
and the Cognitive Core domain Blueprint—are design inputs, not automatically
approved runtime truth. RFCs under [`docs/rfc/`](../rfc/RFC-0001-Knowledge-Engine.md)
are proposals.

## Resolving contradictions

1. Identify each source, its status, date/commit, and exact claim.
2. Preserve the higher-authority approved intent, but use code/tests to describe
   what executes now. Never rewrite runtime history to match a design document.
3. If executable behavior violates a governing document, record the mismatch as
   debt/risk and stop before architectural change.
4. Consult Git to determine chronology and whether one source superseded another.
5. Resolve a material design conflict through an ADR; update code, normative
   documents, and operational state together only after approval.
6. Chats may explain context but cannot override repository evidence.

Known contradiction at this checkpoint: Luxiom is the confirmed product
identity in the Product North Star and recent Git history, while README,
`pyproject.toml`, `app/core/config.py`, and many historical documents still use
JARVIS-OS/JARVIS. This pack records but does not resolve that migration.

Sprint 22 evidence exists only in the
`feat/sprint-22-durable-local-knowledge` working tree at this checkpoint. The
base tag remains `sprint-21-complete`; no Sprint 22 commit, merge, or tag is
claimed. Constitution and ADR statuses remain unchanged.

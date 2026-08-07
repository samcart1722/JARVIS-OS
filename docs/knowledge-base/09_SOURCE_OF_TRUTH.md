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

Sprint 27 is fully released. Its functional merge is
`758e63278f0b342302dd1ed0d41f8514d1d9f1c3`; release-truth governance merged
through PR #30; and annotated tag `sprint-27-complete`, object
`35a198af85299e9e09d086e63f66020ccdc522d3`, points to release commit
`1501183b4c40faaba278f8d61f875d65954223a7`. The verified release backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260807_160935`. Sprint 27 is the latest
completed tagged release; Sprint 26 remains the prior completed tagged release
at `sprint-26-complete`. Constitution and ADR statuses remain unchanged.

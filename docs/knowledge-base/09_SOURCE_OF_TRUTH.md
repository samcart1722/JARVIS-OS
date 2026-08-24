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
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260807_160935`.

Sprint 28 Durable Actor–Workspace Membership Foundation v1 is the prior
immutable completed tagged implementation release. Its annotated tag
`sprint-28-complete`, object
`986ae13ca8fefcbd6197db8a723e25ae4e3dc62a`, points to implementation release
commit `be22ffddda6d6961497c338caadf4c85e0fcb3ed`. Sprint 27 remains valid
historical release lineage; Sprint 26 remains the earlier completed tagged
release at `sprint-26-complete`. Sprint 28 release-truth metadata governance and
final closure are historical governance context.

Sprint 29 Git release truth is tag `sprint-29-complete`, object
`c3a204555cc512ae9404039aeb8be8d6aa421550`, commit
`9590beca0ddfce544f774ffc1327d01f8044a420`, tree
`57914fd7451d2c5c1c46251bfc7721cc06f8461a`, and approved fingerprint
`0210c787df64fec2f44d5004309d3f73ea5aabfac1322792b0ea34c2c1742b73`.
The sole authoritative backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_141402`: bundle/ZIP/manifest
SHA-256 values are `21f6ede11b901891f871854182aa7998ad9fd16f3ab269adf8d01436ea679e7c`,
`d6b2a6b3434514357621aef90c224a88a94c0dd9a49ea0024c68d6b9ee3e4441`, and
`95a23b025654d269d55e392833a5eda843f0043420fd37a8436120761b9c9438`.
`LUXIOM_20260818_140013` is `FAILED_VERIFICATION /
NON_AUTHORITATIVE_RELEASE_BACKUP`; its hashes and LF-to-CRLF diagnostic
fingerprint are forensic only.

Sprint 30 Git release truth is governed tag
`governed-sprint-30-complete`, which peels to ordinary PR #37 merge commit
`6181f549c12195c69708ee2cfa53399a46fa4b29`. Its authoritative recoverable
backup is `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_SPRINT30_20260819_173314`.
Sprint 30 release-truth governance closure completed before the Sprint 31 base.

Sprint 31 - Durable Action Permission Foundation v1 is the latest governed
implementation release. PR #40 merged at
`9cad78ed22f0a6aef26eda0623d0f544cf65e5be`, and immutable governed tag
`governed-sprint-31-complete` peels to that commit. Authoritative backup
`LUXIOM_20260821_095503` is verified and recoverable. Independent review was
unavailable and no independent implementation review is claimed.

Release-truth synchronization commit
`d79552f9ab19d7b2da9f2a60be4ef48b8b9608cd` merged through PR #41 at ordinary
canonical merge `7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`. Mandatory canonical validation
passed 117 architecture and 1,119 repository tests, Ruff, and
`git diff --check`. The merged implementation and release-truth branches were
deleted locally and remotely. The RT2B documentation diff received independent
post-edit approval, and PR #41 received independent pre-merge approval; neither
is independent implementation review. PR #42 received final independent
pre-merge approval and merged through ordinary two-parent merge commit
`fa90defc44ad756a33f11e470105db57a440e201`. Final canonical validation passed
117 architecture and 1,119 repository tests, Ruff, and `git diff --check`. All
governed Sprint 31 implementation, release-truth, and closure working branches
were merged and cleaned locally and remotely before this post-closure
documentation record. Final governance verification confirmed the closure
conditions. Sprint 31 is formally governance-closed at canonical closure
checkpoint `fa90defc44ad756a33f11e470105db57a440e201`. This record reflects the
already-established closure state and does not create or condition it. No
Sprint 32 implementation is authorized and no Sprint 32 scope is frozen.

For immutable release facts, Git objects, refs, and immutable release tags take
precedence, followed by verified release-backup evidence, active reviewed
repository documentation, the repository canonical checkpoint, and then any
external/live continuity ledger used for active workflow continuity. External
continuity context can never override contradictory Git release truth.
Constitution and ADR statuses remain unchanged.

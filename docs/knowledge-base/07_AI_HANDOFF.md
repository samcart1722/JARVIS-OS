# AI Handoff

## Current Sprint 33 recovery brief

1. **Canonical branch and checkpoint:** `master` at
   `9af9984691b034710243e1da487767108915ce3a`.
2. **Latest governed release:** Sprint 33 — Durable Action Permission
   Revocation Foundation v1.
3. **Baseline, implementation, PR, and tree:** baseline
   `f1e1519eedd6f021cb98c6ac8a9242f6b946b645`, implementation
   `9f4b86beddaa1e2550e054a55e6c743c87f2723c`, PR #48, release tree
   `3a1317dc1a1c295ae5e2b77947a149cf138134ba`.
4. **Tag identity:** `governed-sprint-33-complete`, annotated object
   `4d0774ee5172da9eff0ee246011775980aac367f`, peeling to canonical release
   `9af9984691b034710243e1da487767108915ce3a`.
5. **Capability:** historical `PermissionGrantRepository` remains exactly
   lookup/create; the separate `PermissionGrantRevocationRepository` contains
   exactly `revoke`. `PermissionPolicy` remains authorization-only.
6. **Persistence:** exact, case-sensitive, unnormalized actor/workspace/action
   revocation physically deletes only the exact row. Present and absent both
   commit and return `None`; re-grant remains possible. Schema version is 4.
7. **Boundaries:** no Container, API, `app/local_command`, authentication,
   mapping, membership, routing, or cognitive-fallback revocation ownership.
   No public revoke or permission-management endpoint exists.
8. **Proof:** separate `revoke` and `verify` Python processes used the same
   external SQLite database. Fresh verification storage proved durable absence
   and authorization denial. Same-process tests are supplemental only.
9. **Validation:** 134 architecture and 1,293 repository tests passed. Ruff,
   `compileall`, and `git diff --check` passed. No GitHub CI/status checks were
   present.
10. **Backup:**
    `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260826_122727`; bundle, source ZIP,
    and manifest SHA-256 values are
    `E3CEE9B8156248D3627872D3558DBB56B923BD791E2B9FDE2EB951CBFC8AB7E4`,
    `BB18BDF291BD9DB02C2F19B8AF886187A750A65EDBC98CB0926DC46F68D49576`, and
    `E92D45BA2EA7CB8E8D20C226343308AC55887E1E9FE40F0D726A45550BAF3803`.
    Frozen design contract and sidecar SHA-256 values are
    `A456AEA3F596B18CB2D2D20399845D0079358ACF2A1C13AB477AD553FFFA59F3` and
    `0E34AC2B74FFA1EBAB5B638FBA628E804C60BC5D8F7BBEC01473E811CA44B411`.
11. **Governance:** feature-branch cleanup completed locally and remotely.
    Documentation synchronization is later reporting and cannot move the tag.
    No Sprint 34 scope is authorized or frozen.

## Historical Sprint 32 recovery brief

1. **Identity:** Luxiom is a domain-independent Cognitive Operating System.
   HealthBridge is a product/client, not part of the Core.

2. **Canonical branch:** `master`.

3. **Latest release at this historical checkpoint:** Sprint 32 — Authenticated
   Local Command Application Gateway v1.

4. **Frozen base and implementation commit:**
   `7aa29bdc894fe646d9e76cb0466d2e26fd44bc88` and
   `a56a11f1b92b08df5e310aea749d9cda07570b65`.

5. **PR and ordinary merge commit:** PR #45 merged at
   `08c15e3ee225c4cdb2f382af5464da01d33d3f6d` with parents
   `7aa29bdc894fe646d9e76cb0466d2e26fd44bc88` and
   `a56a11f1b92b08df5e310aea749d9cda07570b65`.

6. **Release tree:** `d9e31be190d8077886ce6f85642f9b89d1fd8529`.

7. **Governed tag, object, and peel:** `governed-sprint-32-complete`, annotated
   object `c1f4267177d316d303c8c4c0e7fd3728afdcad32`, peeling to
   `08c15e3ee225c4cdb2f382af5464da01d33d3f6d`.

8. **Validation:** 129/129 architecture tests and 1273/1273 repository tests
   passed. Ruff and `compileall app tests` passed; closure worktree was clean
   and local `master` equaled `origin/master`.

9. **Authoritative recoverable backup:**
   `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260825_103049`. Complete bundle,
   source ZIP, and manifest SHA-256 values are
   `F1A1CC107C9D2864E767F03BFECB19EE4BE3D03C4061535FBDF30F66B268A07B`,
   `D6F91E1E9B66064CB3928A08D0D8F8B115B69632D20D66C85F77291608868B2F`, and
   `46F4612172505B5AAAC93AEB58CBFF0411C5BB038DBBCC352F122AFA1FAE37CA`.
   Backup verification passed.

10. **Application boundary:** `app/api` → `app/local_command` →
    `AuthenticatedLocalCommandRoutingService` → existing governed downstream
    chain. `POST /local/command` is a bounded local-use development surface;
    historical `/brain/think` and legacy `/knowledge` remain separate.

11. **Secret and fallback semantics:** the proof is secret-aware, never returned,
    and explicitly rejects pickle serialization. Cognitive fallback is a strict,
    required per-request authorization and is never automatic. Unexpected HTTP
    failures use a fixed sanitized envelope.

12. **Composition:** default `Container` remains rejecting, fail-closed,
    in-memory, and construction-time no-I/O. Sprint 32 adds no operational
    SQLite credential composition.

13. **Non-goals:** no production authentication, durable credentials, JWT/OAuth,
    sessions, devices, RBAC, public administration, public Internet exposure,
    CORS, UI, runtime SQLite credential composition, or automatic fallback.

14. **Review truth:** the first independent implementation review found two
    HIGH issues: pickle serialization of proof and incorrect initial manifest
    hash semantics. Both were corrected and explicitly closed by the approving
    second review. Independent staged-index attestation and final independent
    pre-merge review also approved the release.

15. **Approved snapshot evidence:** worktree snapshot
    `47A5B64330FB2DE1502CD32D77593E2389ECF594D1187560FDA08DF15E552A33`;
    staged/committed snapshot
    `2F28B3527701E73986A14331E4763629EDB439EF4A1B5E958FD125EB1F4CAE7E`;
    manifest v2 file
    `97F4E58613511999429D114483821EC110A35C6EACD0F2A4DF8359CE3C59D28C`;
    staged manifest v3 file
    `2ACA626A456D9A8989268C7796D693DFC0654C00A2E08F9D14A7752490FB1043`.

16. **Governance and next implementation:** Sprint 32 is formally closed at
    immutable checkpoint `08c15e3ee225c4cdb2f382af5464da01d33d3f6d`; the
    feature branch was cleaned locally and remotely after verification and
    backup. This later documentation synchronization reports, rather than
    establishes or moves, that closure. No subsequent implementation sprint is
    authorized merely by Sprint 32 closure; any next implementation remains a
    planning and contract-definition boundary until explicitly approved.

## Required recovery order

1. Read `LUXIOM_CANONICAL_PROJECT_STATE.md`.
2. Read `LUXIOM_START_HERE.md`.
3. Verify Git branch, HEAD, `origin/master`, tag object, tag peel, and worktree.
4. Read Product North Star and Cognitive Lifecycle.
5. Read Current State, Runtime Architecture, Decisions and Guardrails,
   Technical Debt, and Roadmap.
6. Run the configured architecture and repository test suites.
7. Compare documentation against executable runtime before proposing changes.

## Non-negotiable guardrails

- The model is not the Core.
- The Core remains domain-independent and infrastructure-independent.
- Local deterministic capability is preferred when sufficient.
- Memory and knowledge belong to Luxiom, not to a model.
- Identity, workspace, membership, and action authorization remain explicit
  and separate.
- Public transport does not silently acquire internal capabilities.
- Do not infer architecture or release truth from old sprint-number collisions.
- Do not move, recreate, delete, or retarget immutable governed release tags.

## Resume instruction

Resume from canonical `master` and verify that local `HEAD` equals
`origin/master` before continuing. Sprint 33 implementation, ordinary merge,
final validation, immutable tagging, backup verification, feature-branch
cleanup, and formal governance closure are complete. The immutable Sprint 33
checkpoint remains `9af9984691b034710243e1da487767108915ce3a` under
`governed-sprint-33-complete`; later documentation commits may advance `master`
without moving it. This instruction does not reopen or condition that closure.
Do not begin a subsequent implementation sprint without explicit authorization;
any next implementation remains a planning and contract-definition boundary
until explicitly approved.

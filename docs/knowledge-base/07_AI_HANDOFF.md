# AI Handoff

## Recovery brief

1. **Identity:** Luxiom is a domain-independent Cognitive Operating System.
   HealthBridge is a product/client, not part of the Core.

2. **Canonical branch:** `master`.

3. **Latest governed implementation release:** Sprint 32 — Authenticated Local
   Command Application Gateway v1.

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
`origin/master` before continuing. Sprint 32 implementation, ordinary merge,
final validation, immutable tagging, backup verification, feature-branch
cleanup, and formal governance closure are complete. The immutable Sprint 32
checkpoint remains `08c15e3ee225c4cdb2f382af5464da01d33d3f6d` under
`governed-sprint-32-complete`; later documentation commits may advance `master`
without moving it. This instruction does not reopen or condition that closure.
Do not begin a subsequent implementation sprint without explicit authorization;
any next implementation remains a planning and contract-definition boundary
until explicitly approved.

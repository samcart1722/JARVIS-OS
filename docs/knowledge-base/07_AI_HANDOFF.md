# AI Handoff

## Current Sprint 38 recovery brief

Implementation `b690e299ac4737f7323fdaf631c459f5f25ce80b`, PR #58,
ordinary two-parent release merge `97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4`.
Parents, in order: `e26b8a6c7b89132b9ff2221b1bc35d0726cba236` and
`b690e299ac4737f7323fdaf631c459f5f25ce80b`.
Release tree `683ee3336b17ec4d63f5b542e1553ddb9e2fb445` equals the approved
feature tree; exactly 36 authorized files changed from the first parent.
Annotated tag `governed-sprint-38-complete`, object
`70e48c1d4ccb813b064136507d44e90c71d752b3`, peels to that release merge.
Exact annotation: `Sprint 38 - Authorized local knowledge browse v1`.

Authorized local knowledge browse v1 adds explicit `knowledge browse :: {}`
through the existing authenticated local command flow. The separate
`knowledge.records.browse` permission precedes a workspace-scoped metadata
lookup. At most 50 summaries expose exactly `record_id`, `kind` and `key`,
with `truncated` derived from a bounded 51st-row lookahead. No value,
provenance, workspace, total or cursor is exposed in the BROWSE projection.
Prepare BROWSE and selection-based Prepare READ only write the editor;
explicit Send submits its exact text. A separate READ rechecks authorization.
STORE/READ/FIND, lists, provenance requirements, local-first terminal behavior,
identity boundaries and SQLite schema v4 remain preserved.

Previously executed evidence, not new code tests in this documentation gate:

- Direct Codex post-merge validation on master at the release merge: **1946 PASS,
  0 FAIL, 0 SKIP**, including architecture; global Ruff and diff checks passed.
  Pytest explicitly excluded the unrelated test, disabled bytecode/cache writes,
  and used an external temporary directory. Runtime data was synthetic/temporary.
- Direct Codex pre-merge review: complete remote 36-file diff; 908 focused tests,
  Sprint 37 Node harness 406 checks, BROWSE harness 65 checks in 13 meaningful
  categories, and real-interpreter comparison passed. Node uses a simulated DOM.
- Operator-reported native acceptance: **PASS, 14 scenarios**, Windows 11 and a
  real browser, sessions 0/1/50/51 plus count 1 with a 9000-character ID.
  Focus, Enter/Space, layout, Prepare versus separate Send, exact editor payload,
  real transport, results, STORE/READ/FIND, Pending/Offline recovery and editor
  preservation passed. The operator used TemporaryDirectory-backed synthetic.sqlite3,
  synthetic data/proof and 127.0.0.1:8765, never a personal database. Codex did not
  personally observe this manual execution.
- Exact browser version and a separately identified native list regression were
  not recorded. Consolidated review classified these as non-blocking; list
  regression is covered by automated evidence. Neither missing fact is inferred.
- Independent block, consolidated and pre-merge reviews approved the implementation;
  commit, push, PR, merge, post-merge validation and tag gates passed. No known
  open functional defects or blocking architecture violations remain.

Frozen contract SHA-256:
`5187858A5C09C796D9D07A28607220E8C696CAD9F8C99EF96E7CF0A8E10C0BE5`.

Sprint 38 is complete at the implementation/tagged-release level.
Sprint 38 implementation is released through merged PR #58 and immutable tag
`governed-sprint-38-complete`. Release-truth synchronization is handled through
[documentation PR #59](https://github.com/samcart1722/JARVIS-OS/pull/59), which is
open and not merged. Its branch, `docs/sprint-38-release-truth`, is published to
origin. The authoritative current documentation HEAD is the head reported by
PR #59; this checkpoint does not pin that mutable head to a documentation SHA.
The PR must receive satisfactory independent review of its current HEAD before
proceeding to the separately authorized Documentation Merge Gate.
Documentation merge remains pending. Post-merge verification and remaining
governance requirements must then be completed before formal closure. Sprint 38
remains formally open until those steps are complete. Sprint 39 is NOT STARTED
and NOT AUTHORIZED; no scope is approved.
Later documentation may advance master without moving the immutable
implementation tag.

No verified Sprint 38 backup is recorded in the supplied gate evidence; the
historical backup-verification gate remains outstanding. The feature branch
`feat/sprint-38-authorized-local-knowledge-browse` remains local and remote at the
feature commit; deletion is not authorized. The unrelated untracked file
`tests/unit/reasoning/entities/test_user_request.py` remains intact, unexecuted,
unstaged and absent from the release. The approved 571-file pre-documentation
inventory matched; the six-file UI intervention preserved 565 earlier files.
Sprint 39 is **NOT STARTED**: no scope selected and no implementation authorized.

## Historical Sprint 37 recovery brief

Implementation `6af885900344e7a89f1e3a93f784c616ae786317`, PR #56,
ordinary two-parent release merge `4dfaff1afdd11ab1258a52671e6799a3a442d16d`.
Parents, in order: `30b724a287c58ac881ddaab202f9b5f0778e1af9` and
`6af885900344e7a89f1e3a93f784c616ae786317`.
Release tree `cb220d0661708af226ffa8faefc5c00bba0fda4c` equals the approved
implementation tree. Annotated tag `governed-sprint-37-complete`, object
`1f5863ef15759829e1fbd06c97deb5a6496ff1e6`, peels to that release merge.

Sprint 37 - Local Knowledge Command Assistance adds development-UI preparation
for STORE, READ and FIND through the existing governed command flow. Preparation
validates explicit text fields and provenance and writes an editable command;
only explicit submission executes it. The visible editor remains authoritative.
Python-compatible whitespace validation, real JSON serialization, Unicode and
8192-code-point command limits, isolated-surrogate rejection in the preparer,
concurrency guards and stale-result clearing preserve existing backend,
authorization, fallback, SQLite and literal result-projection contracts.

Previously approved evidence, not new executions by this documentation change:

- User-reported post-merge validation: `1645 passed in 28.10s`; global Ruff and
  diff checks exited 0.
- Independent reviewer executions: 61 focused tests; Node simulated-DOM harness
  with 406 assertions and 15 interpreter-checked vectors; nine ASGI requests
  through a real runtime with temporary SQLite.
- User-reported Edge InPrivate acceptance: preparation without requests,
  STORE idempotency/conflict, READ, FIND filtering/empty/truncated results,
  keyboard/focus, authentication recovery, concurrency, literal rendering and
  list compatibility. This is separate from Node and reviewer ASGI evidence.
- Zero calls apply to the six instrumented cognitive/provider/chat/readiness
  and requests.get/post boundaries during the nine ASGI cases, not universal
  network traffic or runtime startup. No GitHub checks/statuses were observed;
  an empty aggregate `pending` is not CI approval.
- Initial pytest temporary-directory permission errors were resolved using a
  fresh external basetemp. Functional, CA-01 through CA-12, initial documentation
  and implementation pre-merge reviews were approved.
- Non-blocking future recommendation: assert meaningful vector categories,
  rather than rely only on `passed > 0`; no fixed assertion count is required.

The implementation backup was newly created and verified at
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260908_185059_SPRINT37`.
All-refs bundle verification and restoration into an external mirror passed;
all 566 ZIP file entries match the immutable release inventory and raw Git blob
bytes, with no exclusions or export attributes applied. The bundle includes
pre-cleanup refs. No frozen Sprint 37 B0 file or sidecar was identified or
fabricated; a downloaded state summary is not a contract substitute.
The implementation branch `feat/sprint-37-local-knowledge-command-assistance`
was checked at `6af885900344e7a89f1e3a93f784c616ae786317`, confirmed integrated,
then safely deleted locally and remotely after backup verification.
Sprint 36 tag object `16e1b3ad9f1239c86e2786d81722620fa1b7c289` and destination
`b3e5516e70616d8a5a0b30d5e0f01d07af9b7787` remain unchanged.
This later release-truth synchronization may advance `master`; it does not move
or replace the implementation tag or require another implementation backup.
At the Sprint 37 checkpoint, Sprint 38 had no selected scope or authorized implementation. Planning is a
separate gate.

Read [Backup and Recovery](08_BACKUP_AND_RECOVERY.md) for exact hashes.
The external closure report records the documentation commit/PR/merge after
those identifiers exist; no future merge SHA is embedded here.

## Historical Sprint 36 recovery brief

Implementation `f5cc5bfdb9f263b71370af0c9d38e225e831644f`, PR #54,
ordinary merge `b3e5516e70616d8a5a0b30d5e0f01d07af9b7787`, tree
`e657dcf565b5600b2b26d71aea7e49bc67799168`, tag
`governed-sprint-36-complete`, object
`16e1b3ad9f1239c86e2786d81722620fa1b7c289`, peeling to the merge.

Sprint 36 releases application-owned knowledge STORE/READ/FIND projections.
Public records are limited to `record_id`, `kind`, `key`, and `value`, with
`FACT`, `CONCEPT`, or `STATE`; STORE also reports `created`, READ does not, and
FIND returns ordered records with exact maximum-50 truncation truth. Gateway
correlation follows successful governed execution without reparsing or storage
re-query. Authority and workspace/provenance stay internal. Sprint 35 list
projection compatibility remains intact.

HTTP uses closed explicit mapping; the minimal UI renders separate Knowledge
details safely, clears stale state before CSRF/fetch, and owns no persistence or
authority. No edit/delete, pagination, ranking, fuzzy/semantic search, generic
registry, schema/authority redesign, provider/network, Hermes, or Spatial work
was added.

Full governed validation was `1643 passed / 0 failed`. The backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260902_110324_SPRINT36`. The
implementation feature branch was deleted locally and remotely. At that time,
the next action was separate documentation synchronization; subsequent Sprint
37 planning required separate explicit governance. The docs process cannot move
or recreate the immutable implementation tag or backup.

## Historical Sprint 35 recovery brief

Release baseline `ade9a28d45a34b01e1279bc406b7336234e173e2`, implementation
`fd6ecb3a07c9b640892df40561006d79f531c622`, PR #52, ordinary merge
`c2dbab846cc7116568f59786233b64c0f01ab038`, tree
`c65d2bed9158e2630c0912e398bc09eb30a5405e`, tag
`governed-sprint-35-complete`, object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`, peeling to the merge.

Sprint 35 releases closed list ADD/READ application projections, dedicated HTTP
projections, and safe minimal UI rendering after successful authorized local
resolution. Gateway semantic correlation uses typed intent/result data, not
reparsed text. Canonical text and Sprint 34 transport, authority, persistence,
local-first, and fallback boundaries remain unchanged. No generic/knowledge
projection, Core contract, Hermes, or Spatial implementation was added.

Final validation passed 1,535 repository tests, Ruff, `compileall`, release diff
check, post-merge operational proof, and manual browser acceptance. Governed
backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35`.
This later docs synchronization may advance `master` but cannot move, recreate,
or retarget the tag, create a new Sprint 35 implementation tag/backup, or
authorize Sprint 36.

## Historical Sprint 34 recovery brief

Release baseline `227c03e4f5b824710aebea38c5c6dd705e4ec44a`, implementation
`3f48e7fe9cf311df8b3bd2462a1987f8e732303d`, PR #50, merge
`adbd17d564962c6d22617b5857aaaec7da051b08`, tree
`a82e5c4c56b9fdb8660ef0fd878ea89364514b54`, tag
`governed-sprint-34-complete`, object `ae5557c26a719b4cdedef202a191fe92e15a57d3`.
Development runtime is separate and fixed-loopback; `/local/ui` calls governed
`POST /local/command`. Exact Host/Origin, JSON, CSRF, CSP, no-store, no CORS,
and separate nonpersistent proof entry apply. Storage is the `Path.home()`
development path, schema v4. Two processes proved `alpha`, `beta`, membership
and permission denial. Demo PASS; architecture 144; repository 1433; Ruff and
diff-check PASS; no GitHub checks. Backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260827_165704_SPRINT34`. Resume from the
immutable checkpoint; docs may advance master but cannot move the tag or
authorize Sprint 35.

## Historical Sprint 33 recovery brief

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

Verify current Git refs and the current HEAD of PR #59 before resuming. The
Sprint 38 immutable implementation release remains
`97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4` under
`governed-sprint-38-complete`; the published documentation branch is
`docs/sprint-38-release-truth`. Review the PR's current HEAD independently. Only
if that review approves it may the separately authorized Documentation Merge
Gate proceed. After documentation merge, perform post-merge verification and
complete the remaining governance requirements before formal Sprint 38 closure.
The remote PR is authoritative for its changing HEAD; do not infer a future
documentation merge SHA or use an earlier review as approval of a later HEAD.
Preserve the unrelated untracked test and both feature refs. Do not execute the
test or change tags or branches without separate authorization. No verified
Sprint 38 backup is recorded; verify that gate separately. Sprint 39 is NOT
STARTED and NOT AUTHORIZED; planning or implementation requires explicit
authorization.

# Source of Truth

## Current release truth - Sprint 39

Authorized Local Knowledge Browse Continuation v1 implementation is complete.
Blocks A-F are APPROVED. Sprint 39 is MERGED + TAGGED + BACKED UP + RECOVERY
VERIFIED. All Sprint 39 formal closure prerequisites have been satisfied.
Sprint 39 is FORMALLY CLOSED upon merge of this formal-closure record into master.
Release-truth PR #63 is MERGED at
`1d8d67af8f10ba0c390371ce5c819ab10221edcd`; final closure validation is APPROVED.
Completed prerequisites include Blocks A-F APPROVED, implementation PR #62 MERGED,
post-merge validation PASS, release tag created and verified, backup PASS,
recovery verification PASS, release tree equality PASS, release-truth PR #63
MERGED and final closure validation APPROVED.
Sprint 40 is NOT YET AUTHORIZED and has no assigned scope; Sprint 39 closure
does not authorize Sprint 40.

Implementation: `1e92520f786a0f40b06a0a12348cc5d1a3d85e6f`.
Pre-merge documentation correction: `4c659790c65eb22c63f57fd3817b77a0e9bc31e6`.
PR #62 is MERGED through normal two-parent merge
`27409adc61487015ee6b6bb0198c8256b957b723`. Ordered parents:
`f87f8f6fe77901c49e1622edc8bff87c24966430` and
`4c659790c65eb22c63f57fd3817b77a0e9bc31e6`.
Annotated release tag: `governed-sprint-39-complete`.
Tag object: `21c89a0903c5efe371a4359257ab5f51f92fc301`.
Peeled release commit: `27409adc61487015ee6b6bb0198c8256b957b723`.
Annotation: `Governed Sprint 39 complete`.
Release tree: `8bd5c78f025b9146f01eb055842ccd9892869211`.
Later documentation may advance master without moving this immutable tag.

Initial browse remains `knowledge browse :: {}`. Continuation is
`knowledge browse-after :: {"after_record_id":"..."}`: deterministic read-only
execution in the governed workspace, using `knowledge.records.browse` and
re-authorizing on every explicit Send before data access. Filtering uses the
exact workspace and `record_id > normalized after_record_id`; ascending binary
ordering uses SQLite `COLLATE BINARY`. The anchor need not exist. Internal
lookahead is at most 51 summaries; public output is at most 50 records and
`truncated` is true iff another valid record exists. Public records expose only
`record_id`, `kind` and `key`, never value or provenance. Prepare next page
performs zero requests; explicit Send submits the current editor and remains
the execution/authorization boundary. READ is separately prepared and authorized.
Handled continuation success/failure remains terminal locally.

No persistent cursor, snapshots, page history, Previous navigation, totals,
semantic retrieval, knowledge edit/update/delete, generic pagination framework,
model/provider or external network dependency, Hermes integration or Spatial
interface was introduced.

Post-merge validation at the release: **2221 passed, 0 failed, 0 skipped**,
pytest exit code 0; global Ruff, JavaScript syntax and diff checks PASS.
Node harnesses: command assistance 406, BROWSE 65, BROWSE-AFTER 141 checks.
**NATIVE ACCEPTANCE NOT EXECUTED** remains a documented non-blocking manual/release risk.
Node DOM doubles and simulated fetch checks are not native-browser evidence.

Backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260922_180530_SPRINT39_CLOSURE`.
Full-history bundle `JARVIS-OS_SPRINT39_ALL_REFS.bundle`, SHA-256:
`28C7BC09BA706DCFA9F651FDF00B4C327EC489EA4873F13C6E75754F5B79E4C1`.
Release ZIP `LUXIOM_SPRINT39_RELEASE_SOURCE.zip`, SHA-256:
`271B1ED596538805F390D48DC886AC145B36FF1D14B04DFA517C2B234F7BAF40`.
Custody: `RELEASE_CUSTODY.json` and `BACKUP_SHA256_MANIFEST.txt`.
Recovery:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260922_180530_SPRINT39_RECOVERY`.
Bundle verification, external restore and `git fsck --full`: PASS. All 574 ZIP
files passed inventory, byte and extraction verification. Recovered tag object,
peeled commit and both feature commits match the release. Recovered and live
release trees both equal `8bd5c78f025b9146f01eb055842ccd9892869211`:
**tree equality PASS**.

The current untracked `tests/unit/reasoning/entities/test_user_request.py`
remains unstaged, unmodified, unexecuted and outside Sprint 39 commits, the
release tree and ZIP. Its SHA-256 is
`45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C`.
The canonical `git bundle --all` legitimately retains historical committed
versions of that path; this is not inclusion of the current untracked file.
No history filtering or rewriting occurred. The Sprint 39 feature branch remains
preserved; branch cleanup remains a separate, later gate.

## Historical Sprint 38 governed implementation truth

Implementation `b690e299ac4737f7323fdaf631c459f5f25ce80b`, PR #58,
ordinary two-parent release merge `97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4`.
Parents, in order: `e26b8a6c7b89132b9ff2221b1bc35d0726cba236` and
`b690e299ac4737f7323fdaf631c459f5f25ce80b`.
Release tree `683ee3336b17ec4d63f5b542e1553ddb9e2fb445` equals the approved
feature tree; exactly 36 authorized files changed from the first parent.
Annotated tag `governed-sprint-38-complete`, object
`70e48c1d4ccb813b064136507d44e90c71d752b3`, peels to that release merge.
Exact annotation: `Sprint 38 - Authorized local knowledge browse v1`.

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

Sprint 38 is CLOSED. Its Authorized local knowledge browse v1 implementation
was released through merged PR #58 and immutable tag
`governed-sprint-38-complete`. Documentation PR #59 and the final closure PR
#60 are merged; their release truth is incorporated into `master` at
`a5c92f052cc2eb7294767c1f5514ee54bc4b61ca`. The verified backup and recovery
evidence is recorded at
`C:\\PROYECTOS\\LUXIOM_BACKUPS\\LUXIOM_20260911_191202_SPRINT38_CLOSURE`,
and prior Sprint 38 feature/documentation branches were cleaned locally and
remotely. Formal closure is complete, with no known open functional defects.
Later documentation may advance master without moving the immutable
implementation tag.

Verified Sprint 38 backup and recovery evidence is recorded at
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260911_191202_SPRINT38_CLOSURE`. Both
Sprint 38 branches were removed locally and remotely. The unrelated untracked file
`tests/unit/reasoning/entities/test_user_request.py` remains intact, unexecuted,
unstaged and absent from the release. The approved 571-file pre-documentation
inventory matched; the six-file UI intervention preserved 565 earlier files.

## Historical Sprint 38 documentation identities and authority

### Established immutable identities

The implementation feature, release merge, ordered parents, tag and annotated
tag object are the immutable identities recorded above. The implementation
release merge is the base checkpoint for documentation PR #59.
Already published documentation commits are:

- Initial synchronization: `6e888c973237350fb8e8d9d449c131ff038205d6`,
  `docs: synchronize Sprint 38 release truth`.
- First corrective commit: `25d65b9c142aa6e4ef6af251715c9bb7acc65867`,
  `docs: correct Sprint 38 release truth state`.
- Stabilization commit: `b1bb1d22b8f950ed5c9f650c5cceca8d31b25435`,
  `docs: stabilize Sprint 38 release truth`.
- Closure backup identities and hashes are recorded in
  `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260911_191202_SPRINT38_CLOSURE`.
- Sprint 38 closure backup bundle SHA-256:
  `FAAAA11A50B456B5ABBD3C3BD0B4BD64D5AA8CDB61F5F96885603C0BEF74DD99`.
- Sprint 38 release source ZIP SHA-256:
  `6759BD276D644A151EC584FB10DC895158B4435FEED41AF7EED335DBBC161BA0`.
- Sprint 38 release custody SHA-256:
  `480487B8FE586092BE2A889F35A584EEC302C66B16AE2CF82F2EB654128C20DE`.

PR #59 is the stable document-review reference. These existing commit
identities are historical facts, not assertions of its current or final HEAD.

### Formal state and remaining authorization

Documentation PR #59 and the final closure PR #60 are merged. Their release
truth is incorporated into `master` at
`a5c92f052cc2eb7294767c1f5514ee54bc4b61ca`. The verified Sprint 38 backup and
recovery evidence, and local/remote branch cleanup, are recorded in
[Backup and Recovery](08_BACKUP_AND_RECOVERY.md). Sprint 38 is CLOSED and
formal closure is complete for Sprint 38. Current Sprint 39 release truth is
recorded above; its formal closure is effective upon merge of this record into master.

### Historical documentation reviews - not an operational checkpoint

The first independent review of PR #59 returned BLOCKED because current-state
text still treated the documentation commit, branch publication and PR creation
as pending. That finding motivated the published corrective commit
`25d65b9c142aa6e4ef6af251715c9bb7acc65867`.

The second independent review confirmed that the remote PR contained that
corrective commit, but returned BLOCKED because current-state text and the
handoff still pointed to the earlier documentation gate. That historical finding
motivated the historical corrective patch: replace transient workflow narration
with stable release, open-PR and pending-closure states. These two BLOCKED
verdicts record earlier reviews; they are not the current operational checkpoint
or a verdict on a later HEAD. Review of the effective PR HEAD governs merge
eligibility.

## Historical Sprint 37 governed implementation truth

Implementation `6af885900344e7a89f1e3a93f784c616ae786317`, PR #56,
ordinary two-parent release merge `4dfaff1afdd11ab1258a52671e6799a3a442d16d`.
Parents, in order: `30b724a287c58ac881ddaab202f9b5f0778e1af9` and
`6af885900344e7a89f1e3a93f784c616ae786317`.
Release tree `cb220d0661708af226ffa8faefc5c00bba0fda4c` equals the approved
implementation tree. Annotated tag `governed-sprint-37-complete`, object
`1f5863ef15759829e1fbd06c97deb5a6496ff1e6`, peels to that release merge.

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

[Backup and Recovery](08_BACKUP_AND_RECOVERY.md) records the four exact artifact
hashes and complete ZIP verification. RELEASE_CUSTODY.json uses raw Git blob
identity, never checkout materialization hashes. Prior functional validation,
manual browser evidence and newly executed recovery checks are distinguished
there and in Current State. No frozen B0 file was fabricated.

This synchronization does not assert its own future merge SHA. The final
external closure report records that mutable master checkpoint after merge;
the immutable implementation identity above remains authoritative.

## Historical Sprint 36 governed implementation truth

At that release checkpoint: implementation `f5cc5bfdb9f263b71370af0c9d38e225e831644f`,
PR #54, ordinary merge `b3e5516e70616d8a5a0b30d5e0f01d07af9b7787`, tree
`e657dcf565b5600b2b26d71aea7e49bc67799168`, tag
`governed-sprint-36-complete`, object
`16e1b3ad9f1239c86e2786d81722620fa1b7c289`, peeling to the merge. The release
parents are `644097e1f41b2214e0112775bad899a077df7dce` followed by the
implementation commit. Full governed repository validation was `1643 passed /
0 failed`.

The governed backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260902_110324_SPRINT36`. Its bundle,
source ZIP, and backup-manifest SHA-256 values are respectively
`3393A918F3B515FAA34B672EB2D1A5F50A56F5681C3528999316C56FC4FCF8DA`,
`68964D050298999D568A8582FF45450BB4EDDCF8187E47628DCCB4E3C0F116EE`,
and `59230986C545C8709E07A90D31162F1558F64FA74A752BA663BECB538883A227`.
The implementation feature branch was cleaned locally and remotely.

### Canonical content identity and checkout diagnostics

Canonical per-file release identity uses the Git blob OID, SHA-256 of the raw
Git blob bytes, and raw blob byte length. A raw checked-out filesystem SHA is
environment/materialization scoped when checkout filters such as
`core.autocrlf` transform bytes. Historical pre-commit worktree hashes must not
be described as canonical Git-blob hashes.

The Sprint 36 issue was a **HASH-PROVENANCE CATEGORY ERROR**, not release or
blob corruption, tree or patch mutation, or implementation mutation. Canonical
blob evidence and the final verified release archive remained authoritative.

The immutable implementation release is distinct from this later documentation
synchronization. A docs commit may later advance `master`, but must not move,
recreate, retarget, or redefine `governed-sprint-36-complete`, and creates no
new implementation tag or governed backup. At that checkpoint Sprint 37
planning remained separate.

## Historical Sprint 35 governed implementation truth

At its release checkpoint, the latest implementation was
`fd6ecb3a07c9b640892df40561006d79f531c622`,
PR #52, ordinary merge `c2dbab846cc7116568f59786233b64c0f01ab038`,
tree `c65d2bed9158e2630c0912e398bc09eb30a5405e`, tag
`governed-sprint-35-complete`, object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`, peeling to the merge. Full
repository validation passed 1,535 tests; Ruff, `compileall`, release diff check,
post-merge operational proof, and manual browser acceptance passed. This is not
a claim of GitHub CI.

The governed backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35`, with bundle, ZIP,
manifest, and SHA256SUMS hashes
`4B3548A22F13D134F7102950CA1EE559C7283C7BDEFC3C15F9EF7A09B8D57399`,
`A09CECCC279805AB0EFEDFD5AE262DA61B82B8A8447DCCD6F71DDBD319E7B37D`,
`002E82D659EE341D0EDE13A2D3F261A68AC0108404501BD82307B73A31696EF2`, and
`9D4BE4D6EE69C23AA08B1C2E697E5BF8650746B1BA7C41E8ECBEDFFE7E342AD1`.

The immutable implementation release is distinct from this later documentation
synchronization. A docs commit may advance `master` but cannot move, recreate,
retarget, or redefine the Sprint 35 tag; it creates no new implementation tag
or governed backup and authorizes no Sprint 36 or other implementation sprint.

## Historical Sprint 34 governed implementation truth

At its checkpoint, Sprint 34 release implementation
`3f48e7fe9cf311df8b3bd2462a1987f8e732303d`,
PR #50, merge `adbd17d564962c6d22617b5857aaaec7da051b08`, tree
`a82e5c4c56b9fdb8660ef0fd878ea89364514b54`, tag
`governed-sprint-34-complete`, object `ae5557c26a719b4cdedef202a191fe92e15a57d3`.
Demo, architecture 144, repository 1433, Ruff, and diff-check passed; no GitHub
checks were reported. Backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260827_165704_SPRINT34`.
Precedence remains Git objects/refs/immutable tags -> verified release backup ->
active reviewed docs -> canonical checkpoint -> external continuity context.
This docs sync can advance master but cannot move or redefine the tag.

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

Sprint 31 - Durable Action Permission Foundation v1 is a historical governed
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
already-established closure state and does not create or condition it.

Sprint 32 - Authenticated Local Command Application Gateway v1 subsequently
released through ordinary merge `08c15e3ee225c4cdb2f382af5464da01d33d3f6d`
under immutable tag `governed-sprint-32-complete`. Its later documentation
merges did not move that implementation checkpoint.

At the Sprint 33 release checkpoint, Sprint 33 - Durable Action Permission
Revocation Foundation v1 was the latest governed implementation release.
Implementation commit
`9f4b86beddaa1e2550e054a55e6c743c87f2723c` merged through PR #48 at ordinary
release commit `9af9984691b034710243e1da487767108915ce3a`, tree
`3a1317dc1a1c295ae5e2b77947a149cf138134ba`. Immutable tag
`governed-sprint-33-complete`, annotated object
`4d0774ee5172da9eff0ee246011775980aac367f`, peels to that release commit.
Verified backup `LUXIOM_20260826_122727` is authoritative recovery evidence.

Post-merge validation passed 134 architecture and 1,293 repository tests,
Ruff, `compileall`, and `git diff --check`. GitHub reported no CI/status checks.
The later documentation synchronization reports this release truth but is not
part of the immutable Sprint 33 release and cannot move its tag. No Sprint 34
implementation or scope is authorized or frozen by Sprint 33 closure.

For immutable release facts, Git objects, refs, and immutable release tags take
precedence, followed by verified release-backup evidence, active reviewed
repository documentation, the repository canonical checkpoint, and then any
external/live continuity ledger used for active workflow continuity. External
continuity context can never override contradictory Git release truth.
Constitution and ADR statuses remain unchanged.

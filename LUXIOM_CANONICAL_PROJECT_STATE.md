# Luxiom Canonical Project State

## 1. Purpose and authority

This repository-owned `LUXIOM_CANONICAL_PROJECT_STATE.md` is the durable,
versioned checkpoint for project and release continuity. It supports offline
reconstruction from Git when chat continuity is unavailable.

An external live continuity ledger may be newer or more granular during active
governance gates. The repository checkpoint is synchronized only through
reviewed documentation/release-governance changes; it is not updated after
every conversational micro-gate.

For immutable released facts, authority is ordered as follows:

1. Git objects, refs, and release tags
2. Verified release-backup evidence
3. Active reviewed repository documentation
4. This repository canonical checkpoint
5. External/live continuity ledger for current workflow continuity

An external ledger cannot override contradictory Git release truth.

## 2. Permanent Luxiom vision

Luxiom is a Personal Cognitive Operating System: local-first, offline-capable,
multiuser, multiworkspace, multidevice, multimodal, and action-oriented.
HealthBridge is a product/client built on the domain-agnostic Core, not a reason
to introduce product-domain coupling into it.

Decision order is deterministic capabilities; Luxiom-owned memory/knowledge;
local models only when interpretation, synthesis, or planning adds value; and
network/external models only under explicit policy and authorization. Memory
and knowledge belong to Luxiom, not a model, and remain persistent, traceable,
identity-separated, workspace-separated, permission-separated, and
provenance-aware.

## 3. Non-negotiable architectural principles

- The model is not the Core; providers are replaceable.
- The Core remains domain-agnostic and infrastructure-independent.
- Local deterministic behavior is primary and failures are deny-by-default.
- Identity, workspace, admission, action permission, and provenance remain
  explicit and separate.
- Public transport does not silently acquire internal capabilities.
- Material architecture changes require reviewed governance and, where
  applicable, an ADR.

## 4. Repository and environment identity

- Repository: `samcart1722/JARVIS-OS`
- Local canonical repository: `C:\PROYECTOS\JARVIS-OS`
- Canonical branch: `master`
- Runtime: Python 3.12 or newer; release validation used Python 3.14.6 on
  Windows PowerShell.

## 5. Historical governed release — Sprint 33

Sprint 33 — Durable Action Permission Revocation Foundation v1 is a historical
governed release immediately preceding Sprint 34.

Frozen baseline: `f1e1519eedd6f021cb98c6ac8a9242f6b946b645`

Implementation commit: `9f4b86beddaa1e2550e054a55e6c743c87f2723c`

PR #48 merged through ordinary two-parent release commit
`9af9984691b034710243e1da487767108915ce3a`, with release tree
`3a1317dc1a1c295ae5e2b77947a149cf138134ba`.

Governed tag: `governed-sprint-33-complete`

Annotated tag object: `4d0774ee5172da9eff0ee246011775980aac367f`

The tag peels to the immutable Sprint 33 release commit above.

Sprint 33 adds a separate `PermissionGrantRevocationRepository` containing
exactly `revoke`. The historical `PermissionGrantRepository` remains exactly
`is_granted` and `create`; `PermissionPolicy` remains exactly `is_allowed`.
`SQLitePermissionGrantRepository` structurally implements both persistence
ports, while `RepositoryPermissionPolicy` remains authorization-read-only.

Revocation validates exact actor, workspace, and nonblank string action values,
preserves case and whitespace, and performs one exact physical SQLite `DELETE`.
Present and absent revocations both commit and return `None`, reveal no prior
existence, and leave unrelated grants untouched. Re-grant remains available
through `create`. Declared persistence failures surface through the stable
`PermissionGrantRepositoryError` boundary.

SQLite schema version remains 4. Sprint 33 adds no migration, schema object,
soft-delete state, audit history, expiry, RBAC, public permission administration,
Container management composition, or public revoke endpoint.

The separate operational `revoke` and `verify` phases passed a genuine
two-process proof against the same external SQLite database. Post-merge
validation passed 134 architecture and 1,293 repository tests, Ruff,
`compileall`, and `git diff --check`. GitHub reported no CI/status checks.

Authoritative recoverable backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260826_122727`

Bundle, source ZIP, and manifest SHA-256 values are
`E3CEE9B8156248D3627872D3558DBB56B923BD791E2B9FDE2EB951CBFC8AB7E4`,
`BB18BDF291BD9DB02C2F19B8AF886187A750A65EDBC98CB0926DC46F68D49576`, and
`E92D45BA2EA7CB8E8D20C226343308AC55887E1E9FE40F0D726A45550BAF3803`.
The frozen design contract and sidecar SHA-256 values are
`A456AEA3F596B18CB2D2D20399845D0079358ACF2A1C13AB477AD553FFFA59F3` and
`0E34AC2B74FFA1EBAB5B638FBA628E804C60BC5D8F7BBEC01473E811CA44B411`.
The feature branch was cleaned locally and remotely after release verification.

This later documentation synchronization reports the immutable release; it is
not part of that release and does not move its tag. No Sprint 34 implementation
or scope is authorized or frozen.

### Historical governed release — Sprint 32

At its release checkpoint, Sprint 32 — Authenticated Local Command Application
Gateway v1 was the latest governed implementation release.

Frozen base: `7aa29bdc894fe646d9e76cb0466d2e26fd44bc88`

Implementation commit: `a56a11f1b92b08df5e310aea749d9cda07570b65`

PR #45 ordinary two-parent merge:
`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`

Merge parents: `7aa29bdc894fe646d9e76cb0466d2e26fd44bc88` and
`a56a11f1b92b08df5e310aea749d9cda07570b65`

Release tree: `d9e31be190d8077886ce6f85642f9b89d1fd8529`

Governed tag: `governed-sprint-32-complete`

Annotated tag object: `c1f4267177d316d303c8c4c0e7fd3728afdcad32`

The tag peels to immutable Sprint 32 checkpoint
`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`. Later documentation commits may
advance `master` without moving, recreating, or retargeting that tag.

Post-merge validation passed 129 architecture tests and 1,273 repository tests.
Ruff and `compileall app tests` passed; the worktree was clean and local
`master` equaled `origin/master`.

Authoritative recoverable backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260825_103049`

Complete Git bundle SHA-256:
`F1A1CC107C9D2864E767F03BFECB19EE4BE3D03C4061535FBDF30F66B268A07B`

Source ZIP SHA-256:
`D6F91E1E9B66064CB3928A08D0D8F8B115B69632D20D66C85F77291608868B2F`

Backup manifest SHA-256:
`46F4612172505B5AAAC93AEB58CBFF0411C5BB038DBBCC352F122AFA1FAE37CA`

Backup verification passed. The feature branch was deleted locally and
remotely only after merge, post-merge validation, tag verification, and backup.

Sprint 32 releases this dependency direction:

`app/api` → `app/local_command` →
`AuthenticatedLocalCommandRoutingService` → existing governed downstream chain.

It adds a framework-independent `app/local_command` boundary, the bounded
local-use `POST /local/command` development surface, closed application request,
result, and error contracts, strict explicit cognitive-fallback authorization,
fixed sanitized unexpected-error handling, secret-aware proof handling, and
explicit rejection of pickle serialization. Default `Container` composition
remains rejecting, fail-closed, in-memory, and construction-time no-I/O.

Sprint 32 does not add production authentication, durable credentials,
JWT/OAuth, sessions, device lifecycle, RBAC, public administration, public
Internet exposure, CORS, UI, runtime SQLite credential composition, or
automatic cognitive fallback. Historical `/brain/think` and legacy
`/knowledge` remain separate and were not made authenticated by Sprint 32.

The first independent implementation review required correction because proof
material remained pickle-serializable and the initial external manifest hash
semantics were incorrect. Both HIGH findings were corrected and explicitly
closed by the approving second independent review. Independent staged-index
attestation and final independent pre-merge review also approved the release.
The approved worktree and committed snapshot SHA-256 values are respectively
`47A5B64330FB2DE1502CD32D77593E2389ECF594D1187560FDA08DF15E552A33` and
`2F28B3527701E73986A14331E4763629EDB439EF4A1B5E958FD125EB1F4CAE7E`.
Approved manifest v2 and staged manifest v3 file SHA-256 values are respectively
`97F4E58613511999429D114483821EC110A35C6EACD0F2A4DF8359CE3C59D28C` and
`2ACA626A456D9A8989268C7796D693DFC0654C00A2E08F9D14A7752490FB1043`.

Sprint 32 is formally governance-closed at the immutable checkpoint above.
This later documentation synchronization reports that already-established
closure; it does not establish, condition, or move the release checkpoint.

### Historical governed release — Sprint 31

Sprint 31 — Durable Action Permission Foundation v1 is the historical release
immediately preceding Sprint 32.

Frozen base: `a2ba79dc5deb70e6929cf4164ea8a0636ffc0dc9`

Feature implementation commit:
`0796cb54ee1d570852a85722af43b1b41a3b4881`

PR #40 ordinary merge: `9cad78ed22f0a6aef26eda0623d0f544cf65e5be`

Release tree: `5ad6dc854c546e82cdab6c6fd5a5c48072b7fc0d`

Governed tag: `governed-sprint-31-complete`

Annotated tag object: `2f52c2973bd349bd4302d7bb1e59307f5b14708c`

The tag peels to the release commit above.

Post-merge validation passed 117 architecture tests and 1,119 repository
tests. Global Ruff and `git diff --check` passed.

Authoritative recoverable backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260821_095503`

Bundle SHA-256:
`5FD5D98735DA2C770F685B813C4777200E4D5DE3E3902E6EBD0FE459A56C7022`

Source ZIP SHA-256:
`485BCC969008BD841EAA4F34A2BCA8E6DDE8EB96208CCB4A64605B06FC1E73C6`

Manifest SHA-256:
`5996D7AA4D2181C79AC7409E48E7A654C19D0691BC809BCB5C6678B28D1D6BBF`

Bundle recovery reproduced the exact release commit, tag object, tag peel,
release tree, `master`, and clean worktree.

Sprint 31 released durable exact actor/workspace/action permission persistence
behind the existing `PermissionPolicy` boundary. Authentication,
principal-to-actor mapping, workspace selection, membership admission, and
action authorization remained distinct. Membership alone granted no action.
Default `Container` composition remained no-I/O; durable permission storage
required explicit repository injection.

Independent implementation review was unavailable and no independent review is
claimed. Same-assistant technical and adversarial reviews identified and
corrected a schema-verification defect before release.

Release-truth synchronization commit
`d79552f9ab19d7b2da9f2a60be4ef48b8b9608cd` merged through PR #41 at ordinary
merge `7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`. Canonical post-merge validation
passed 117 architecture tests, 1,119 repository tests, Ruff, and
`git diff --check`. The merged implementation and release-truth branches were
deleted locally and remotely. The RT2B documentation diff received independent
post-edit approval, and PR #41 received independent pre-merge approval; neither
is an independent review of the Sprint 31 implementation.

PR #42 merged through ordinary two-parent merge commit
`fa90defc44ad756a33f11e470105db57a440e201`. Final canonical validation passed
117 architecture tests, 1,119 repository tests, Ruff, and `git diff --check`.
All governed Sprint 31 implementation, release-truth, and closure working
branches were merged and cleaned locally and remotely before the post-closure
documentation record. Formal Sprint 31 governance closure conditions were
satisfied at that canonical checkpoint. Independent implementation review
remains unavailable and is not claimed.

### Historical predecessor — Sprint 30

Sprint 30 — Durable Principal–Actor Mapping Foundation v1 was released at
governed implementation release commit
`6181f549c12195c69708ee2cfa53399a46fa4b29` under immutable governed tag
`governed-sprint-30-complete` (annotated tag object
`cd410e5e0ddad708cd3b1a8b91b0fe4dc38e5f35`).

## 6. Historical immutable release — Sprint 28

Sprint 28 Durable Actor–Workspace Membership Foundation v1 is implemented,
independently approved, merged, post-merge validated, tagged, tag-verified, and
backed up with an independently verified recovery proof.

## 7. Sprint 28 architecture and contract boundaries

- Membership is not authentication or action authorization.
- `ActorIdentity` is not identity proof; `WorkspaceIdentity` is not access proof.
- Trusted binding is not durable membership.
- Active membership is workspace admission only.
- `PermissionPolicy` remains downstream action authorization.
- Default `Container` membership composition is in-memory and no-I/O.
- SQLite is infrastructure pointing inward; it stores current membership state,
  not permissions or audit history.
- No public authentication/JWT/OAuth/session/RBAC or public
  membership/FastAPI transport was added.
- No model, provider, readiness, or network dependency was introduced.

## 8. Sprint 28 implementation and review evidence

Final independent review: APPROVED. Validation passed 28 SQLite, 41 membership,
29 Container, 130 trusted-context, 156 focused Sprint 28, 78 architecture, and
915 repository tests. Ruff and diff checks were clean. Both demos passed with
model/provider/readiness/network calls of `0 / 0 / 0 / 0`.

## 9. Sprint 28 Git, PR, and merge identifiers

- Feature parent: `a2f68902928e45a8cecb774660cdeec25ddf6a69`
- Feature branch: `feat/sprint-28-durable-actor-workspace-membership`
- Feature commit: `95341198145f84d80c7cf37bf73b707cfe574a21`
- Pull request: `#32`
- Merge method: normal two-parent merge commit
- Canonical merge commit: `be22ffddda6d6961497c338caadf4c85e0fcb3ed`

## 10. Sprint 28 tag evidence

- Tag: `sprint-28-complete`
- Annotated tag object: `986ae13ca8fefcbd6197db8a723e25ae4e3dc62a`
- Peeled release commit: `be22ffddda6d6961497c338caadf4c85e0fcb3ed`
- Message: `Sprint 28 complete — Durable Actor–Workspace Membership Foundation v1`

The tag is immutable and must never be moved, deleted, recreated, force-updated,
or retargeted. Later documentation commits may advance `master` without moving
the tag.

## 11. Sprint 28 verified backup evidence

- Directory: `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260817_190455`
- Bundle: `LUXIOM_SPRINT_28_RELEASE.bundle` (`670834` bytes)
- Bundle SHA-256: `803b9b247352c73a4d3131d047db4f1f681dfcfa3772d8af89c404f69841bebf`
- Source ZIP: `LUXIOM_SPRINT_28_SOURCE.zip` (`586096` bytes)
- ZIP SHA-256: `35270e40daa0094c4d8061bf7f1f58db575e4e2b0bd08367d93099cf467d586d`
- Manifest: `LUXIOM_SPRINT_28_RELEASE_MANIFEST.txt` (`1601` bytes)
- Manifest SHA-256: `35026303a205a964f0eae08b6ba735c37236c0fb5d7c392f675ea0921b36f0dc`
- Tag-tree/ZIP count: `501 / 501`; missing `0`; unexpected `0`
- Independent bundle recovery: PASS

## 12. Current deliberate deferrals and technical debt

Roles/RBAC, groups, inheritance, wildcards, explicit deny rules, permission
update/expiry/audit history, public authentication transport, production
credential technology, sessions/devices, public permission administration,
encryption/retention/synchronization, remote identity providers, cloud sync,
and broader semantic retrieval remain deferred.

Durable exact action-permission persistence itself is no longer deferred:
Sprint 31 releases that bounded capability.

Exact durable action-permission revocation is also no longer deferred: Sprint
33 releases exact current-state removal. General permission lifecycle
administration, soft-delete/history, revoker identity, and synchronization
remain deferred.

## 13. Governance workflow

Implementation, independent review, commit, push/PR, pre-merge review, governed
merge, post-merge validation, immutable tag, tag verification, verified backup,
and reviewed release-truth synchronization are separate gates. Never infer
authorization for a later gate from completion of an earlier one.

## 14. Session resume checklist

1. Read this checkpoint and `LUXIOM_START_HERE.md`.
2. Verify branch, HEAD, working-tree cleanliness, `origin/master`, and tags.
3. Confirm immutable release identifiers directly from Git.
4. Verify backup evidence when recovery matters.
5. Read Current State, Runtime Architecture, Decisions, Technical Debt, and
   Roadmap before proposing scope.
6. Sprint 35 is formally closed. Do not begin Sprint 36 or any other subsequent
   implementation sprint without explicit authorization; the next
   implementation remains a planning and contract-definition boundary until
   explicitly approved.

## 15. Repository checkpoint synchronization policy

Update this checkpoint only in a reviewed documentation/release-governance
change when durable project or release truth materially changes. Do not use it
as a conversational scratchpad or mirror every external-ledger update.

## 16. Historical Sprint 33 closure state

- Sprint 33 implementation is complete through PR #48 and ordinary merge
  `9af9984691b034710243e1da487767108915ce3a`.
- Post-merge validation passed 134 architecture and 1,293 repository tests,
  Ruff, `compileall`, and `git diff --check`.
- Immutable governed tag `governed-sprint-33-complete`, annotated object
  `4d0774ee5172da9eff0ee246011775980aac367f`, peels to the merge checkpoint.
- Authoritative backup `LUXIOM_20260826_122727` is verified and recoverable.
- Independent implementation and pre-merge reviews approved the release.
- The Sprint 33 feature branch was cleaned locally and remotely.
- Sprint 33 is formally governance-closed at the immutable checkpoint above.
- This later post-closure documentation synchronization reflects that
  already-established state; it does not establish, condition, or move closure.
- No subsequent implementation sprint is authorized merely by this checkpoint.

## 17. Historical governed release — Sprint 34

At its release checkpoint, Sprint 34 — Local Interactive Runtime & Minimal UI
Foundation v1 was current.
Frozen baseline `227c03e4f5b824710aebea38c5c6dd705e4ec44a` and implementation
`3f48e7fe9cf311df8b3bd2462a1987f8e732303d` reached PR #50, ordinary
two-parent release `adbd17d564962c6d22617b5857aaaec7da051b08`, tree
`a82e5c4c56b9fdb8660ef0fd878ea89364514b54`, and immutable tag
`governed-sprint-34-complete` (object
`ae5557c26a719b4cdedef202a191fe92e15a57d3`, peeling to the release).

The development-only Windows/Uvicorn runtime is a separate FastAPI composition
fixed to `127.0.0.1:8765`. `/local/ui` uses exact Host, exact POST Origin
`http://127.0.0.1:8765`, strict JSON, runtime CSRF, CSP, no-store local assets,
no CORS, and same-origin `POST /local/command` through the existing gateway and
downstream authorities. The ordinary app/router remain separate. Proof is read
with `getpass`, entered again manually in the browser, and never transferred or
persisted. Normal development storage is `Path.home() / ".luxiom" /
"development" / "local-interactive" / "luxiom-local.sqlite3"`; `Path.home()`
is the sole application-level OS-home resolver. Schema stays v4 with no
migration. Lifecycle is `NEW -> STARTED -> CLOSED`, close is idempotent, failed
startup ends closed, missing gateway uses historical fallback, and invalid
explicit injection fails closed. Cognitive fallback stays off by default and
there is no public structured list-result projection.

Separate OS-process proof passed HTTP write/read for exact `alpha`, `beta`,
membership 403 `access_denied`, and permission 403
`local_permission_denied`, using controlled external databases. Post-merge:
operational demo PASS, architecture 144, repository 1433, Ruff PASS, and
`git diff --check` PASS; no GitHub checks were reported.

Backup `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260827_165704_SPRINT34` has bundle,
ZIP, manifest, and sums hashes `23915918709261911ca01c11d90b3d35b6c240c95df6b709fc2b55e65df677a8`,
`5ffdb1157b5bc333b97aed42175086f563b2eabcedc95bfa0bdba6d775925d9d`,
`b8408b013857fb584af619681080a0c6fa4db98aa98b4c27a8302430e91d315d`,
and `1ec182ebb47c34a9fc9eaf7e6499724aa8742e0626aa952f0e7c6f85b1bd794e`.
Frozen design/sidecar hashes are `0e695aaa3f337187b0b5c503359afe6fadd4676d026aee87338b8103cf8cc01a`
and `b905791ee11791c55417981473119b78486fdf42b72cf9ed8441daa4290b09b3`.
This docs sync is outside the immutable release, cannot move its tag, and
authorizes no Sprint 35.

## 18. Current governed release — Sprint 35

Sprint 35 — Structured Local List Result Projection v1 is current. Baseline
`ade9a28d45a34b01e1279bc406b7336234e173e2` and implementation
`fd6ecb3a07c9b640892df40561006d79f531c622` reached PR #52 and ordinary
two-parent release `c2dbab846cc7116568f59786233b64c0f01ab038`, with parents
`ade9a28d45a34b01e1279bc406b7336234e173e2` and
`fd6ecb3a07c9b640892df40561006d79f531c622`. The release tree is
`c65d2bed9158e2630c0912e398bc09eb30a5405e`. Immutable tag
`governed-sprint-35-complete`, annotated object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`, peels to the release merge.

Successful authorized list operations now flow from the already interpreted
typed intent and structured local result through the closed application union
`LocalListAddProjection | LocalListReadProjection`, dedicated ADD/READ HTTP
models, and safe minimal UI rendering. `LocalCommandApplicationGateway` alone
owns semantic correlation and never reparses command text. ADD projects
`list_id`, `added`, `already_present`, and `items`; READ projects `list_id` and
`items`, including an empty list. When absent, HTTP omits only `projection` and
preserves the historical explicit null behavior of the four-field envelope.
Canonical responses remain `List updated locally.` and `List read locally.`

The UI displays the applicable list fields, renders empty collections as exact
em dash `—`, clears stale projection state synchronously before fetch or early
CSRF return, hides ADD-only rows for READ, and renders hostile values literally via
safe DOM/text operations. Sprint 34 authentication, mapping, workspace,
membership, routing, `PermissionPolicy`, capability, loopback transport, CSRF,
SQLite, local-first, and fallback boundaries remain unchanged. Sprint 35 adds
no generic or knowledge projection, Cognitive Core contract, Core/schema,
authentication/membership/permission, browser persistence, provider/network,
Hermes, or Spatial expansion.

Final validation passed 1,535 repository tests, Ruff, `compileall`, and release
diff check. Post-merge operational proof and manual browser acceptance passed.
The frozen design and sidecar SHA-256 values are
`0FA3E67B5993799C0AAC4B699A50D74B66DF2BCB43AC67F16BCDDA77E40BF07B`
and `157B7CD7270D57DD7D9AD1C445B6F24BB3CD39CDCD2CCF3956B09FE81A717CD1`.

Governed backup
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35` has bundle,
release ZIP, manifest, and SHA256SUMS hashes
`4B3548A22F13D134F7102950CA1EE559C7283C7BDEFC3C15F9EF7A09B8D57399`,
`A09CECCC279805AB0EFEDFD5AE262DA61B82B8A8447DCCD6F71DDBD319E7B37D`,
`002E82D659EE341D0EDE13A2D3F261A68AC0108404501BD82307B73A31696EF2`,
and `9D4BE4D6EE69C23AA08B1C2E697E5BF8650746B1BA7C41E8ECBEDFFE7E342AD1`.
This later documentation synchronization is outside the immutable release. It
may advance `master`, but cannot move, recreate, or retarget its tag, creates no
new Sprint 35 implementation tag or governed backup, and authorizes no Sprint
36 or other implementation sprint.

## 19. Sprint 29 immutable release checkpoint

PR `#34` merged feature `8f08583701571e69b6d18a0cfea64d073201a217`
(base `779a2719eaf83de2f98134cc76027dd6f2e7d945`) at
`9590beca0ddfce544f774ffc1327d01f8044a420`, tree
`57914fd7451d2c5c1c46251bfc7721cc06f8461a`. Annotated tag
`sprint-29-complete`, object `c3a204555cc512ae9404039aeb8be8d6aa421550`,
peels to the merge. The approved 28-path fingerprint is
`0210c787df64fec2f44d5004309d3f73ea5aabfac1322792b0ea34c2c1742b73`.

The sole authoritative backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_141402`; bundle, raw Git-blob ZIP,
and manifest SHA-256 are `21f6ede11b901891f871854182aa7998ad9fd16f3ab269adf8d01436ea679e7c`,
`d6b2a6b3434514357621aef90c224a88a94c0dd9a49ea0024c68d6b9ee3e4441`, and
`95a23b025654d269d55e392833a5eda843f0043420fd37a8436120761b9c9438`.
Verification matched 518/518 raw blobs. `LUXIOM_20260818_140013` is
`FAILED_VERIFICATION / NON_AUTHORITATIVE_RELEASE_BACKUP`; `git archive` under
the verified Windows `core.autocrlf=true` configuration converted 460 LF blobs
to CRLF, so its hashes and diagnostic fingerprint are forensic only.

The released flow is opaque proof → local authentication → principal → explicit
actor mapping → explicit workspace selection → membership admission → local
routing → `PermissionPolicy` action authorization → capability. Authentication,
membership, and authorization remain separate; `PrincipalIdentity` is not
`ActorIdentity`. The trusted binding path remains separate and non-authenticated.
Configured authentication is local, process-local, nonpersistent, and demo
oriented; production credentials and durable/public/multidevice authentication
remain deferred. SQLite remains schema v2. Validation passed 75 authentication,
39 Container, 9 demo-unit, 104 architecture, 129 trusted/membership, 278 focused,
and 1,035 repository tests; Ruff, the 8/8 authenticated demo, and the 7/7 trusted
demo passed with zero remote calls. At the Sprint 29 checkpoint, the next sprint
remained an unfrozen planning and contract-definition boundary.

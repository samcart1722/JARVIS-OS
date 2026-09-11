# Backup and Recovery

## Sprint 38 release custody status - backup verification pending

The immutable implementation is PR #58 merge
`97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4`, tree
`683ee3336b17ec4d63f5b542e1553ddb9e2fb445`. Annotated tag
`governed-sprint-38-complete`, object
`70e48c1d4ccb813b064136507d44e90c71d752b3`, peels to that merge;
local and remote tag identities were directly verified during the tag gate.

No authoritative Sprint 38 backup bundle, source ZIP, custody manifest or restore
verification is recorded in the supplied gate evidence. Do not label Sprint 37
artifacts below as Sprint 38 backups. The external B5 inventory/snapshot is
implementation-review evidence, not a verified release backup. Backup creation
and verification remain a separate governance gate, not performed by this
documentation synchronization. Feature refs and the unrelated local test remain
preserved.

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

No project should depend on one computer, chat account, or AI provider. Git and
repository documentation preserve continuity; chats are secondary history.

## Backup layers

- **GitHub remote:** keep code, branches, tags, and history in an access-controlled
  remote. Verify the remote and push intentionally; the local backup script
  never uploads anything.
- **Local clone:** maintain a working clone and periodically verify `git status`,
  HEAD, and remote tracking.
- **Git bundle:** a portable single file containing all refs reachable through
  `git bundle create --all`; verify it with `git bundle verify`.
- **Compressed snapshot:** captures working files, including uncommitted
  documentation/code, while excluding Git internals, environments, caches,
  backups, secrets, and temporary artifacts.
- **Documentation:** keep North Star, lifecycle, ADRs, Knowledge Base, and sprint
  summaries in Git and in the snapshot.

## Backup script

Run from the repository root:

```powershell
# Preview only; creates nothing
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\backup_luxiom.ps1 -DryRun

# Default destination: sibling directory ..\LUXIOM_BACKUPS
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\backup_luxiom.ps1

# Explicit destination and latest known test result for the manifest
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\backup_luxiom.ps1 `
  -DestinationPath 'E:\LuxiomBackups' `
  -TestStatus '9 passed, 1 pytest cache warning'
```

Each real run creates `LUXIOM_yyyyMMdd_HHmmss` containing
`luxiom-repository.bundle`, `luxiom-source.zip`, and `MANIFEST.txt`. It warns
when the working tree is dirty. Use a destination outside the repository.

## Sprint 37 verified immutable-release backup

Directory: `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260908_185059_SPRINT37`.

Exactly four artifacts:

- `JARVIS-OS_SPRINT37_ALL_REFS.bundle`: `731E8B80ADE2A36952F869A1CD7D0BB7F85D0D2138E9AC9FC942DAA65AA32E85`
- `LUXIOM_SPRINT37_RELEASE_SOURCE.zip`: `2064B8099D40013A192A3DF075D506232B6EDE783A9EDE07083A727CA9A06E91`
- `RELEASE_CUSTODY.json`: `D5341736A4B6177376E53358F84B53364B984431728824286E8123EC90EADB99`
- `BACKUP_SHA256_MANIFEST.txt`: `35B3AAD003E185AD8A94685E7B7A5F25C97FE59EA1424B84BF69C3DB68BFF4C5`

The SHA-256 manifest lists the other three artifacts; its own hash above is
reported separately, with no self-reference. Every hash was recomputed after
writing. The all-refs bundle was verified with git bundle verify and restored
into an external mirror. Release commit, both ordered parents, release tree,
Sprint 37 tag object/target and Sprint 36 tag custody matched Git.

The ZIP was built directly from raw blobs at
`4dfaff1afdd11ab1258a52671e6799a3a442d16d`; all 566 file entries, their inventory,
byte lengths and bytes match the release and restored bundle. No exclusions
were applied; export-ignore/export-subst checks found no applied attributes.
This is not the general script's filtered working-tree snapshot. Tracked tests
and .env.example are source; no local credentials, databases or test-run data
were copied. Historical bundle paths include a Python-source memory.zip;
versioned paths and credential signatures were screened, not universally audited.

RELEASE_CUSTODY.json records commands, outcomes, limits and per-file blob OIDs,
raw-blob SHA-256 values and lengths. Checkout CRLF/LF hashes are not substituted
for Git-blob identity. No frozen B0 contract or sidecar was identified for
Sprint 37; neither was invented. A downloaded project-state summary is not a
contract or checkpoint replacement.

External closure evidence and the final report are stored separately at
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260908_185059_SPRINT37_CLOSURE_EVIDENCE`.
GATE2_VERIFIED.json records the restored mirror location; the custody manifest
also records it. GATE3_BRANCH_CLEANUP.json records safe implementation-branch
deletion after recovery verification. The backup retains pre-cleanup refs.
Later documentation integration does not move the tag, modify this backup or
require a second implementation backup. Sprint 36 backup remains untouched.

## Sprint 36 verified recovery checkpoint

Directory:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260902_110324_SPRINT36`.

The governed checkpoint contains exactly six files: the all-refs bundle, source
ZIP from the immutable release, frozen design contract and sidecar, release
custody manifest, and backup SHA-256 manifest.

- `BACKUP_SHA256_MANIFEST.txt`:
  `59230986C545C8709E07A90D31162F1558F64FA74A752BA663BECB538883A227`
- `JARVIS-OS_SPRINT36_ALL_REFS.bundle`:
  `3393A918F3B515FAA34B672EB2D1A5F50A56F5681C3528999316C56FC4FCF8DA`
- `LUXIOM_SPRINT36_RELEASE_SOURCE.zip`:
  `68964D050298999D568A8582FF45450BB4EDDCF8187E47628DCCB4E3C0F116EE`
- Frozen contract:
  `E05B66B6E4814BB342AEBF7B317C3408F500EF4C4BCF5AA62C665BFF3F49D358`
- Frozen sidecar:
  `3C7E1373082AFCF3E6DC1ABBE2067A94BAFC920EDAAA94344818D12D23D43EE9`

The bundle and immutable tag are restorable, and all 14 governed ZIP members
matched canonical Git blob bytes. This is the Sprint 36 implementation backup;
later documentation synchronization neither changes nor replaces it.

## Sprint 35 verified recovery checkpoint

Directory:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35`.

- Governed bundle SHA-256:
  `4B3548A22F13D134F7102950CA1EE559C7283C7BDEFC3C15F9EF7A09B8D57399`
- Release ZIP SHA-256:
  `A09CECCC279805AB0EFEDFD5AE262DA61B82B8A8447DCCD6F71DDBD319E7B37D`
- Manifest SHA-256:
  `002E82D659EE341D0EDE13A2D3F261A68AC0108404501BD82307B73A31696EF2`
- SHA256SUMS SHA-256:
  `9D4BE4D6EE69C23AA08B1C2E697E5BF8650746B1BA7C41E8ECBEDFFE7E342AD1`

The backup records release merge
`c2dbab846cc7116568f59786233b64c0f01ab038`, tree
`c65d2bed9158e2630c0912e398bc09eb30a5405e`, and immutable tag
`governed-sprint-35-complete`, annotated object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`, peeling to the release merge. The
frozen design SHA-256 is
`0FA3E67B5993799C0AAC4B699A50D74B66DF2BCB43AC67F16BCDDA77E40BF07B`.
This is the governed Sprint 35 implementation backup; later documentation
synchronization does not create or require another implementation backup.

## Sprint 34 verified recovery checkpoint

Directory: `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260827_165704_SPRINT34`.
Bundle `23915918709261911ca01c11d90b3d35b6c240c95df6b709fc2b55e65df677a8`;
release ZIP `5ffdb1157b5bc333b97aed42175086f563b2eabcedc95bfa0bdba6d775925d9d`;
manifest `b8408b013857fb584af619681080a0c6fa4db98aa98b4c27a8302430e91d315d`;
SHA256SUMS `1ec182ebb47c34a9fc9eaf7e6499724aa8742e0626aa952f0e7c6f85b1bd794e`.
Frozen design/sidecar: `0e695aaa3f337187b0b5c503359afe6fadd4676d026aee87338b8103cf8cc01a`,
`b905791ee11791c55417981473119b78486fdf42b72cf9ed8441daa4290b09b3`.
The bundle contains complete history and tag. The ZIP came from
`governed-sprint-34-complete`, object `ae5557c26a719b4cdedef202a191fe92e15a57d3`,
peeling to `adbd17d564962c6d22617b5857aaaec7da051b08`.

## Sprint 33 verified recovery checkpoint

The verified Sprint 33 release backup is:

`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260826_122727`

- Bundle SHA-256:
  `E3CEE9B8156248D3627872D3558DBB56B923BD791E2B9FDE2EB951CBFC8AB7E4`
- Source ZIP SHA-256:
  `BB18BDF291BD9DB02C2F19B8AF886187A750A65EDBC98CB0926DC46F68D49576`
- Manifest SHA-256:
  `E92D45BA2EA7CB8E8D20C226343308AC55887E1E9FE40F0D726A45550BAF3803`

The backup corresponds to immutable tag `governed-sprint-33-complete`, annotated
object `4d0774ee5172da9eff0ee246011775980aac367f`, peeling to release commit
`9af9984691b034710243e1da487767108915ce3a`. Verify these identities and hashes
during recovery; do not move or recreate the governed tag.

## Secret safety

The snapshot excludes `.env`, `.env.*` variants (while allowing the safe
template `.env.example`), common key/certificate/credential files, virtual
environments, caches, logs, and temporary artifacts. The script does not inspect
or copy `.env` content and never uses the network. Still review new secret file
naming conventions and `git status` before every backup. Store actual secrets
in a password manager or approved secret vault, separately from code backups.
Never place recovery credentials in `MANIFEST.txt` or conversation summaries.

## Recovery on a new computer

1. Install Git, PowerShell, and a supported Python (metadata currently requires
   Python 3.12+).
2. Prefer cloning the trusted GitHub remote. If unavailable:

   ```powershell
   git clone .\luxiom-repository.bundle LUXIOM
   cd LUXIOM
   git bundle verify ..\luxiom-repository.bundle
   ```

3. If uncommitted files matter, extract `luxiom-source.zip` to a separate
   directory, inspect it, and selectively copy the needed files into the clone.
4. Restore secrets separately from the approved vault; do not recover them from
   the snapshot.
5. Read `LUXIOM_START_HERE.md` and the Knowledge Base.
6. Create the environment and install declared dependencies.
7. Verify branch/HEAD/tags, `git status`, and the manifest; run pytest.

## Recovery with another account or AI

Provide access to the restored repository, not to secret material. Paste the
recovery prompt from [AI Handoff](07_AI_HANDOFF.md). Require the new AI to read
the repository, inspect Git/runtime/tests, and confirm the checkpoint before
making changes. Archived chats may be supplied for background but cannot
override repository evidence.

## Post-restore verification

- `git bundle verify <bundle-path>`
- compare manifest commit/branch/tags with `git log` and `git tag`
- `git status --short --branch`
- `.\.venv\Scripts\python.exe -m pytest`
- confirm normative and Knowledge Base files open and relative links resolve
- scan the restored snapshot for unexpected secret files before sharing it

## Frequency and naming

Recommended minimum: push reviewed commits after each work session; create a
portable backup at every sprint closure and before architecture/migration work;
create a weekly backup during active development; retain periodic monthly
copies offline. Use:

`LUXIOM_yyyyMMdd_HHmmss`

Keep at least one copy on a physically different device or trusted encrypted
storage. Test a restoration periodically; an untested backup is only a hope.

## Conversations

Chats may be archived locally as PDF or Markdown. Commit concise decision or
sprint-closure summaries only when useful. Important decisions belong in
normative documents/ADRs and executable evidence, never solely in a chat. See
[`history/conversations/README.md`](history/conversations/README.md).

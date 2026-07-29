# Backup and Recovery

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

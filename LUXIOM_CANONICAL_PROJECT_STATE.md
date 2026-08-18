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

## 5. Recent release lineage

Sprint 27 released Trusted Request Context Foundation v1 at
`sprint-27-complete`. Sprint 28 builds on it with durable actor/workspace
membership admission. Earlier sprint summaries preserve historical lineage.

## 6. Latest immutable release — Sprint 28

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

Authentication and principal proof, durable action-permission storage,
roles/invitations, transition/audit history, public trusted/membership
transport, encryption/retention/synchronization policy, and broader semantic
retrieval remain deferred. These are not implied Sprint 29 commitments.

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
6. Do not begin Sprint 29 without explicit authorization.

## 15. Repository checkpoint synchronization policy

Update this checkpoint only in a reviewed documentation/release-governance
change when durable project or release truth materially changes. Do not use it
as a conversational scratchpad or mirror every external-ledger update.

## 16. Current closure state

- Implementation complete and final independent review approved
- Merged and post-merge validated
- Immutable release tag independently verified
- Release backup independently recovered and verified
- Release-truth documentation synchronized in this candidate tree
- Metadata change still requires independent review and later governed
  commit/push/PR/merge
- Feature-branch cleanup not performed
- Final release closure not yet declared
- Sprint 29 not authorized

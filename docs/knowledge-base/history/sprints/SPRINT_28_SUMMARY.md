# Sprint 28 — Durable Actor–Workspace Membership Foundation v1

## Objective and implementation

Sprint 28 adds exact actor/workspace admission while preserving downstream
action authorization. Block A established immutable contracts and the in-memory
lifecycle. Block B made membership mandatory after trusted-context resolution
and corrected inherited cache hygiene. Block C added SQLite schema v2, durable
parity, explicit injection, and a review-found migration atomicity correction.
Block D added architecture enforcement, a two-process durable proof,
documentation, and final validation.

## Frozen boundaries

Membership uses canonical identities, exact case-sensitive pairs, ACTIVE and
INACTIVE state, `get/create/activate/deactivate`, no delete, and stable errors.
Create never reactivates inactive state. Membership is workspace admission,
not authentication, identity proof, access proof, or action authorization.
Trusted binding is not durable membership; `PermissionPolicy` remains
downstream. SQLite persists current state only. Default `Container` is
in-memory/no-I/O; durable storage is explicit caller-owned injection. Schema v2
is additive and rollback-safe from v1.

No public authentication, JWT, OAuth, session, RBAC, membership/FastAPI
transport, model/provider/network dependency, or `CognitiveEngine` coupling was
introduced.

## Review, merge, and validation

Final independent implementation review was APPROVED. Feature commit
`95341198145f84d80c7cf37bf73b707cfe574a21`, parent
`a2f68902928e45a8cecb774660cdeec25ddf6a69`, changed exactly 40 paths and
merged through PR #32 using normal merge commit
`be22ffddda6d6961497c338caadf4c85e0fcb3ed`. Its parents are the prior master
and feature commit, respectively.

Post-merge validation passed 28 SQLite, 41 membership, 29 Container, 130
trusted-context, 156 focused Sprint 28, 78 architecture, and 915 repository
tests. Ruff and diff checks were clean. Both demos passed; external
model/provider/readiness/network calls were `0 / 0 / 0 / 0`.

## Immutable tag and verified backup

- Tag: `sprint-28-complete`
- Annotated tag object: `986ae13ca8fefcbd6197db8a723e25ae4e3dc62a`
- Peeled release commit: `be22ffddda6d6961497c338caadf4c85e0fcb3ed`
- Tag message: `Sprint 28 complete — Durable Actor–Workspace Membership Foundation v1`
- Tag verification: APPROVED
- Verified backup: `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260817_190455`
- Bundle SHA-256: `803b9b247352c73a4d3131d047db4f1f681dfcfa3772d8af89c404f69841bebf`
- Source ZIP SHA-256: `35270e40daa0094c4d8061bf7f1f58db575e4e2b0bd08367d93099cf467d586d`
- Manifest SHA-256: `35026303a205a964f0eae08b6ba735c37236c0fb5d7c392f675ea0921b36f0dc`
- Bundle recovery and exact 501-file ZIP/tree comparison: PASS

## Closure state and deferrals

Implementation, review, merge, validation, tag verification, and backup
verification are complete. This release-truth metadata change still requires
independent review and later governed commit/push/PR/merge. Feature-branch
cleanup and final governance closure have not occurred.

Authenticated principals, durable action permissions, roles/invitations,
transition/audit history, and public transport remain deliberate deferrals.
Sprint 29 is not authorized and has not started.

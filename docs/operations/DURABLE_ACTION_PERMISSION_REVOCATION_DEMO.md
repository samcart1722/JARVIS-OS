# Durable Action Permission Revocation Demo

Status: Sprint 33 governed-release operational proof.

## Purpose

This proof demonstrates durable exact action-permission revocation across two
separate Python interpreter processes using the same external SQLite database.

It is operations-only evidence, not a public permission-administration or
revocation interface.

## Prerequisites

- A local Python environment with project dependencies installed.
- An explicit SQLite database path outside the repository.

Repository-local paths are rejected with:

`Demo database must be outside the repository.`

## Process 1 — revoke

Run from the repository root:

```powershell
python scripts/demo_durable_action_permission_revocation.py revoke --database <PATH>
```

Expected scenarios:

- `exact-grant-created-and-allowed`
- `exact-grant-revoked`
- `authorization-denied-after-revoke`

Recorded formal result: all three scenarios `PASS`; `Overall: PASS`; exit code
`0`.

The process creates the exact fixed grant, proves authorization, revokes it,
proves denial, closes storage, and exits successfully.

## Process 2 — verify

After Process 1 exits, start a separate Python interpreter invocation against
the same database:

```powershell
python scripts/demo_durable_action_permission_revocation.py verify --database <SAME_PATH>
```

Expected scenarios:

- `exact-grant-remains-absent`
- `authorization-remains-denied`

Recorded formal result: both scenarios `PASS`; `Overall: PASS`; exit code `0`.

The verify process constructs fresh storage, performs normal open/schema
verification, creates a fresh repository and policy, and proves durable absence
and denial.

## Fixed proof values

- Actor: `durable-permission-revocation-actor`
- Workspace: `durable-permission-revocation-workspace`
- Action: `list.items.read`

## Boundaries

The proof uses `SQLiteLocalStorage`, `SQLitePermissionGrantRepository`, and
`RepositoryPermissionPolicy` directly. It does not involve Container, API,
local-command routing, authentication, mapping, membership, cognitive engine,
model/provider, or network behavior.

Two separate interpreter invocations are required for the formal cross-process
claim. Same-process unit tests provide supplemental coverage only and are not
the cross-process proof.

The historical Sprint 31 durable grant-persistence demo remains separate and
unchanged. This Sprint 33 proof does not add a public permission-management
surface or authorize any later sprint.

# Sprint 28 — Durable Actor-Workspace Membership Foundation v1

## Objective and four-block plan

Sprint 28 adds exact actor/workspace admission while preserving downstream
permission authorization. Block A established immutable contracts and the
in-memory lifecycle. Block B made membership mandatory after trusted-context
resolution and corrected inherited cache hygiene. Block C added schema v2,
SQLite durability, parity, injection, and a review-found migration atomicity
correction. Block D adds architecture enforcement, a two-process durable proof,
documentation synchronization, and final validation.

## Frozen contract

Membership uses canonical identities, exact case-sensitive pairs, ACTIVE and
INACTIVE state, `get/create/activate/deactivate`, no delete, and stable errors.
Create never reactivates inactive state. Membership is neither authentication
nor permission. SQLite persists current state only; permissions remain separate.
Default Container composition is in-memory/no-I/O; durable storage is explicit
caller-owned injection. Schema v2 is additive and rollback-safe from v1.

Public API, CognitiveEngine, providers, and authentication remain unchanged.
The cumulative feature-tree scope is 40 changed/new paths when all Block D
artifacts are present. Final counts belong to the Block D implementation and
independent-review reports. Current implementation validation is 915 full-suite
tests, 78 architecture tests, 156 focused Sprint 28 tests, Ruff clean, diff
check clean, and both manual demos passing with zero external calls.

- IMPLEMENTED
- UNCOMMITTED
- UNMERGED
- UNTAGGED
- UNRELEASED
- FINAL INDEPENDENT REVIEW PENDING

Authenticated principals, durable permissions, roles/invitations, audit
history, and public transport remain deferred. The Block C atomicity issue was
found during review and corrected, not deferred.

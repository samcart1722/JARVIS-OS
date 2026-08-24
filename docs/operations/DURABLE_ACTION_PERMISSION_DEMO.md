# Durable Action Permission Demo

Status: Sprint 31 governed-release operational proof.

This internal two-process proof demonstrates exact SQLite-backed action
authorization while preserving authentication, principal mapping, workspace
selection, membership, routing, and local-capability boundaries.

It is not RBAC, role management, credential persistence, authentication
transport, session management, a grant/revoke API, or a public API.

## Database location

The caller must use a SQLite database outside the repository.

Seed command:

.\.venv\Scripts\python.exe -B scripts\demo_durable_action_permission.py seed --database C:\PROYECTOS\LUXIOM_TEST_TEMP\durable-action-permission-demo.sqlite3

Verify command:

.\.venv\Scripts\python.exe -B scripts\demo_durable_action_permission.py verify --database C:\PROYECTOS\LUXIOM_TEST_TEMP\durable-action-permission-demo.sqlite3

## Seed phase

Seed proves:

- durable principal-to-actor mappings are written independently;
- required durable memberships are written independently;
- one exact actor/workspace/action grant can be created;
- exact duplicate creation conflicts instead of overwriting;
- actor, workspace, and action matching remains exact and case-sensitive;
- durable list state is stored independently from authorization state.

## Verify phase

Verify opens the same SQLite database in a new process and proves:

- exact-durable-permission-success -> local_success
- wrong-workspace-denied -> local_permission_denied
- wrong-action-denied -> local_permission_denied
- wrong-actor-denied -> local_permission_denied
- permission-repository-failure-denied -> local_permission_denied

Denied authorization reaches neither list read nor list add.

CognitiveEngine fallback does not execute.

## Zero-call evidence

The final verify counters must remain:

Model calls: 0
Provider calls: 0
Readiness calls: 0
Network calls: 0
Overall: PASS

## Durable permission schema

SQLite schema v4 stores each permission as exactly:

actor_id + workspace_id + action

It stores no role, credential, proof, verifier, secret, token, session,
permission expiry, audit history, wildcard, or inheritance rule.

The demo database may be deleted by the caller after the proof.

This document records governed Sprint 31 operational behavior.

Sprint 31 merged through PR #40 and is released at
`governed-sprint-31-complete`. Release-truth and closure-truth integration,
final canonical validation, governed working-branch cleanup, and final
governance verification are complete. Formal Sprint 31 governance closure
conditions were satisfied at canonical checkpoint
`fa90defc44ad756a33f11e470105db57a440e201`; the demo behavior is unchanged.

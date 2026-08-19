# Durable Principal-Actor Mapping Demo

This internal two-process proof demonstrates durable SQLite-backed
`PrincipalIdentity -> ActorIdentity` mapping.

It is not credential persistence, authentication proof storage, membership,
RBAC, action authorization, account lifecycle, or a public API.

Use a caller-owned database outside the repository:

```powershell
.\.venv\Scripts\python.exe -B scripts\demo_durable_principal_actor_mapping.py seed --database C:\PROYECTOS\LUXIOM_TEST_TEMP\principal-actor-demo.sqlite3
.\.venv\Scripts\python.exe -B scripts\demo_durable_principal_actor_mapping.py verify --database C:\PROYECTOS\LUXIOM_TEST_TEMP\principal-actor-demo.sqlite3
```

Seed proves:

- one exact principal can create one actor mapping;
- duplicate creation conflicts instead of overwriting;
- multiple principals may map to the same actor;
- principal matching remains exact and case-sensitive.

Verify opens a new storage instance and proves:

- the primary durable mapping routes successfully;
- a second principal sharing the same actor routes successfully;
- a case-variant principal remains unmapped and fails closed with
  `principal_mapping_failed`;
- successful mapping still requires workspace selection, membership admission,
  downstream `PermissionPolicy`, and the local capability path.

The verify phase additionally uses the existing durable membership repository
to complete the downstream route. Sprint 30 adds no membership persistence
behavior.

Model, provider, readiness, and network totals must all remain zero.

The SQLite table stores only `principal_id` and `actor_id`. It stores no
credential, proof, verifier, secret, token, workspace, role, permission,
membership state, or session.

No FastAPI, Ollama, Redis, or external database server is required. The caller
may later remove only the external demo database it supplied.

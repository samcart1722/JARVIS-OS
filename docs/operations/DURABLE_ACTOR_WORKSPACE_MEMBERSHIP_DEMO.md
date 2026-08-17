# Durable Actor-Workspace Membership Demo

This internal two-process proof demonstrates SQLite-backed current membership.
It is not authentication, identity proof, RBAC, or a public API.

Use a caller-owned database outside the repository:

```powershell
.\.venv\Scripts\python.exe -B scripts\demo_durable_membership.py seed --database C:\PROYECTOS\LUXIOM_TEST_TEMP\membership-demo.sqlite3
.\.venv\Scripts\python.exe -B scripts\demo_durable_membership.py verify --database C:\PROYECTOS\LUXIOM_TEST_TEMP\membership-demo.sqlite3
```

Seed persists active, inactive, and deliberately absent pairs. Verify opens a
new storage instance and proves active/permitted success,
`membership_not_found`, `membership_inactive`, active/no-grant
`local_permission_denied`, workspace isolation, and payload-workspace override
rejection. Model/provider/readiness/network totals must all be zero.

No FastAPI, Ollama, Redis, or external database server is required. The caller
may later remove only the external demo database it supplied.

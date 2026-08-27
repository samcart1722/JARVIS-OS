# Architecture Decision Record — Local Interactive Runtime and Loopback UI

Status: Proposed

## Context

Before Sprint 34, LUXIOM possessed governed local-command capabilities, authentication, principal mapping, membership, permissions, and durable local storage. It lacked a minimal interactive local runtime and UI proving that entire stack as one user-operable flow.

## Decision

Provide a separate interactive FastAPI application bound only to fixed `127.0.0.1:8765`. It uses the same governed `/local/command` path and injects an application gateway through app state only for interactive composition; the historical ordinary application behavior remains unchanged. One `LocalInteractiveRuntime`, backed by SQLite local storage, is started and closed by application lifespan. A minimal browser UI is a development interface, launched by the normal Windows launcher through a programmatic Uvicorn server. The normal launcher uses a persistent per-user development database; the operational proof uses only an external proof database. This decision does not expand the public contract with structured results.

The normal launcher derives its database path exactly as:

```text
Path.home()
/ ".luxiom"
/ "development"
/ "local-interactive"
/ "luxiom-local.sqlite3"
```

`Path.home()` is the sole application-level home authority. The launcher does not explicitly consult environment variables as a parallel or override resolution mechanism. This location is development-only and is not the final production storage architecture.

## Security boundary

The server enforces exact Host validation, requires the exact POST Origin `http://127.0.0.1:8765` for `POST /local/command`, enforces strict JSON Content-Type, a per-process CSRF value delivered by `/local/ui`, and Content Security Policy. It enables no CORS and serves only local assets. The development proof is entered manually in the launcher and again in the browser; it is not transferred from launcher to browser and is not persisted in SQLite, a file, a URL, or an environment variable. No public or LAN bind is permitted. The development proof is not production authentication.

The UI does not own authorization. Each request still passes through authentication, principal mapping, workspace selection, membership, interpretation and routing, `PermissionPolicy`, and local capability and storage. There is no direct UI or repository authorization bypass.

## Process and lifecycle

Uvicorn `Server.run` occupies the main thread. One secret-free readiness and browser helper thread cannot reach the Server, app, runtime, proof, database, or CSRF value. Lifespan owns runtime start and close. Browser-open failure does not stop the server, Ctrl+C performs normal shutdown, and there is no shutdown endpoint.

## Operational evidence

The B6 durability proof used process 1 to perform governed HTTP list additions and then close. Process 2 was a fresh OS process using the same database and performed a governed HTTP list read. Operations/test-only direct observation then found exactly `alpha` and `beta`. Direct observation supplements the HTTP proof and does not replace it.

The denial proof also demonstrated inactive membership producing HTTP 403 `access_denied`, and revoked `list.items.read` permission with membership still active producing HTTP 403 `local_permission_denied`. Both used the correct authentication proof and the real governed HTTP path.

## Consequences

Positive consequences are a user-operable local runtime, a real end-to-end governed path, persistence across launches and processes, maintained authorization boundaries, no production or public-server commitment, and groundwork for future UI work.

Tradeoffs and limitations are development proof material rather than production authentication, a fixed loopback host and port, a minimal UI, canonical text public responses, no structured local result projection, and a development database location that is not final production storage policy.

## Non-goals

This decision does not include production authentication, durable credentials, JWT or OAuth, LAN/remote/public serving, CORS expansion, Electron or Tauri, an installer, service or tray operation, voice or vision, the Spatial interface, Hermes integration, schema v5, structured local-command result projection, an admin or shutdown endpoint, or cloud synchronization.

## Operations demo boundary

`app/operations/local_interactive_demo_runtime.py` and `scripts/demo_local_interactive.py` are operations/test demonstration facilities. They are not product runtime APIs or user configuration interfaces.

## Evidence and validation

Local and independent validation includes B1 runtime lifecycle tests, B2/B3 interactive application and transport tests, B4 UI and security tests, B5 launcher tests, B6 operational tests, and an independent two-process manual proof. At B6-R1, the full suite reported 1423 passed and Ruff reported PASS. Transient execution times are not architectural guarantees.

## Future candidate

STRUCTURED LOCAL COMMAND RESULT PROJECTION remains a future candidate without an assigned Sprint. It is not part of the current implementation or Sprint scope.

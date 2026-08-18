# Internal Local Principal Authentication Demo

> **INTERNAL DEVELOPER DEMO.** `ConfiguredLocalPrincipalAuthenticator` is a
> deterministic process-local adapter for development, tests, and demos. It is
> not production authentication.

## Purpose and scope

This demo exercises the Sprint 29 candidate's existing authenticated internal
routing boundary without Internet, Ollama, an external model, a server, a
database file, filesystem persistence, environment credentials, time, or
randomness.

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -B scripts\demo_local_principal_authentication.py
```

The safe output contains eight stable scenario identifiers, `PASS` or `FAIL`,
stable status codes, stage call counts, four zero remote totals, and an overall
result. It never displays authentication proofs or configured verifier values.

## Scenarios

1. `authenticated-active-permitted` completes the local list read.
2. `authentication-failure-precedes-invalid-workspace` stops at authentication.
3. `mapping-failure-precedes-invalid-workspace` stops at principal mapping.
4. `workspace-selection-invalid` rejects invalid explicit workspace selection.
5. `membership-not-found` stops before routing.
6. `membership-inactive` stops before routing.
7. `authenticated-active-permission-denied` reaches downstream authorization
   and preserves `local_permission_denied` without repository access.
8. `authenticated-payload-workspace-override-rejected` preserves the existing
   `invalid_knowledge_fields` workspace-payload guardrail.

## Security and semantic boundary

`LocalAuthenticationProof` is an opaque authentication-boundary input.
`PrincipalIdentity` is not `ActorIdentity`; principal-to-actor mapping is
explicit. Authentication does not select or authorize workspace admission.
Workspace selection is explicit, membership is workspace admission only, and
`PermissionPolicy` remains downstream action authorization. Authentication
creates neither membership nor `PermissionGrant`.

Sprint 29 authenticates no public FastAPI endpoint. It adds no password, PIN,
API-key, JWT, OAuth, session, cookie, device, biometric, or remote-identity
technology, and no durable credential, principal, or mapping persistence. The
older trusted request-context route remains separate and non-authenticated.

Production credential verification, secure secret management, durability,
recovery, sessions/devices, public transport, and remote identity integration
remain explicit future work.

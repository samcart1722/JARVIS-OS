# Deterministic Local Knowledge Commands Demo

Run from the repository root with `DEBUG=true`:

```powershell
.\.venv\Scripts\python.exe -m scripts.demo_local_knowledge_commands
```

The thin CLI constructs the real in-memory `Container` with reasoning disabled.
The operations runtime receives only the existing text router, actors and
workspace; it constructs no Container, Settings, provider, infrastructure,
SQLite, HTTP or network client.

Nine scenarios demonstrate initial store, identical idempotent store, exact
read with caller-supplied provenance, immutable conflict, not-found, permission
denial, terminal malformed authorized input, unrelated denied fallback and
unrelated authorized deterministic cognition. Spies around the actual composed
boundaries observe cognitive calls `0/0/0/0/0/0/0/0/1`; model-provider,
Ollama-client, readiness and `requests` network calls are all zero.

The JSON grammar never accepts workspace. Workspace is supplied by the routing
request. This is strict structured-command parsing, not natural-language
understanding, and public HTTP is not involved.

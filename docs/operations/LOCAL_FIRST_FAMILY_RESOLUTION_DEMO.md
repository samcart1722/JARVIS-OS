# Local-First Family Resolution Demo

Run with Ollama stopped; no readiness or network access is performed:

```powershell
.\.venv\Scripts\python.exe scripts\demo_local_first_family_resolution.py `
  --actor-id wife --workspace-id family-home
```

The synthetic scenario adds diapers, Gerber and grapes, reads them, rejects a
case-insensitive duplicate of grapes while adding milk, and proves a denied
actor receives no disclosure or mutation. Output reports the local route,
model calls `0`, and external calls `0`. Data is process-local and ephemeral.

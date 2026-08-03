# Deterministic Local Command Interpretation Demo

Run from the repository root with `DEBUG=true`:

```powershell
.\.venv\Scripts\python.exe scripts\demo_local_command_interpretation.py
```

The thin CLI constructs the real in-memory `Container` with reasoning disabled;
the operations runtime receives only the composed router and explicit actor and
workspace. It constructs no Container, Settings, provider, infrastructure,
SQLite, or HTTP client.

The demo reports these five scenarios:

1. **Scenario 1:** valid add is `interpreted`, routes locally, mutates the list,
   and records zero cognitive calls.
2. **Scenario 2:** valid read is `interpreted`, routes locally, returns the
   expected items, and records zero cognitive calls.
3. **Scenario 3:** malformed list syntax is `invalid` and terminal even with
   fallback authorized; it records zero cognitive calls.
4. **Scenario 4:** unrelated text is `not_interpreted`; denied fallback produces
   `safe_insufficiency` and zero cognitive calls.
5. **Scenario 5:** unrelated text is `not_interpreted`; authorized fallback
   selects the cognitive route, succeeds deterministically with reasoning
   disabled, and records one cognitive call.

The visible cognitive count is a route-contract count; unit tests independently
observe the actual processor invocation. Model calls, external calls, readiness
calls, and network calls remain zero. Public HTTP is not involved.

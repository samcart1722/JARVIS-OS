# Durable Local Knowledge Demo

Use a database path outside the repository and run the phases as separate
processes. PowerShell example:

```powershell
$db = Join-Path $env:TEMP "luxiom-sprint-22-demo.sqlite3"
& .\.venv\Scripts\python.exe -m scripts.demo_durable_local_knowledge seed --database $db
& .\.venv\Scripts\python.exe -m scripts.demo_durable_local_knowledge verify --database $db
```

`seed` creates the parent directory explicitly, opens storage, checks and
initializes schema v1, writes and validates the acceptance list and knowledge
record, and closes in `finally`. Its output says only that durable state was
seeded; it does not claim isolation or denial checks. `verify` requires the file
to exist, opens a new runtime, and checks exact list order/display, exact
provenance, workspace isolation, and denied reads and writes. Only `verify`
prints that isolation and denial were verified.

Exit codes are `0` for the complete expected result, `1` for a safely reported
runtime/storage failure, and `2` for invalid arguments. Output exposes no raw
SQL, paths, provider URLs, internal exceptions, or stack traces.

The printed call counters describe the controlled runtime. Automated tests also
patch the actual Ollama generation, readiness, and HTTP request boundaries and
prove zero calls. The demo has no public HTTP exposure, natural-language
routing, external access, or automatic reasoning fallback.

The database is not encrypted and has no synchronization, deletion, retention,
backup, or migration product workflow. Stored provenance is not truth
certification, and no semantic retrieval or automatic ingestion is provided.

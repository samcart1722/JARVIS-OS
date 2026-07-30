# Explicit Scoped Memory Update Demo v1

## Purpose

This runbook demonstrates a deliberate, ephemeral write to Luxiom's scoped
memory after runtime composition. It compares reasoning before and after the
same explicit records are appended under the same explicit scope.

It demonstrates readiness gating, a separate write contract, opt-in update
policy, scope isolation, insertion order, later retrieval, and memory-aware
prompt use. It does not demonstrate durable persistence, automatic learning,
automatic extraction, truth validation, ranking, identity, HTTP updates, or
production concurrency.

## Prerequisites

- Use the repository virtual environment.
- Start Ollama locally.
- Install the model configured by `OLLAMA_MODEL`.
- Use only synthetic, non-sensitive data.

The demo never installs Ollama, pulls a model, or retries.

## PowerShell command

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_memory_update.py `
  --memory-scope "demo-session-1" `
  --remember "Luxiom separates its Cognitive Core from providers." `
  --remember "HealthBridge is the first product planned on Luxiom." `
  "Explain what Luxiom is and mention its first product."
```

CLI arguments may remain in PowerShell history, process inspection, terminal
logs, or support captures. Do not use credentials, secrets, personal or
medical data, or confidential business information.

## Approximate successful output

```text
Luxiom Explicit Scoped Memory Update Demo v1
--------------------------------------------
Provider readiness: ready
Explicit memory scope: yes
Records requested: 2
Records written: 2
Persistence: none

BEFORE EXPLICIT MEMORY UPDATE
Success: true
Response:
...

AFTER EXPLICIT MEMORY UPDATE
Success: true
Response:
...
```

The comparison is observational. Generated responses can vary, and the demo
does not claim that the after response is better or that supplied content is
true.

## Controlled failures and exit codes

When readiness fails, no cognitive execution or memory update occurs.
`provider_unavailable` or `model_unavailable`, the canonical safe message,
zero records written, and exit code 1 are shown.

An unexpected write failure stops the sequence before the after execution.
The CLI prints a safe operational failure and does not expose the exception,
scope, provider response, prompt, URL, or stack trace.

A structured cognitive failure remains visible as `Success: false`, its stable
code, and canonical safe message.

- `0`: readiness is ready, every requested write completes, and both outcomes
  are successful.
- `1`: readiness, writing, either outcome, or another operational step fails.
- `2`: argparse rejects missing or invalid arguments.

## Explicit update semantics

`MEMORY_UPDATE_ENABLED` is independent and false by default. The demo creates a
local revalidated Settings instance with reasoning, retrieval, prompt context,
and update explicitly enabled. It constructs one Container with an initially
empty scoped repository.

After readiness, the engine runs once before writing. Each `--remember` then
causes exactly one `ScopedMemoryRecord` and one writer `add` call, in argument
order. Exact duplicates are allowed and produce separate records. The engine
then runs once after writing with the same prompt and scope.

There is no write during construction, readiness, retrieval, reasoning, prompt
building, provider execution, HTTP handling, or the before execution. Nothing
is extracted from model responses and no model decides what to remember.

## Literal demo retrieval adaptation

The repository performs literal substring matching. The CLI transparently
wraps each synthetic payload using the same Sprint 15 format:

```text
[DEMO RETRIEVAL KEY]
<exact prompt>

[USER-PROVIDED REFERENCE]
<exact payload>
```

This makes the explicit record query-addressable without changing repository
semantics. The payload is preserved, no hidden fact is added, and the scope
identifier is never serialized into records, prompts, reports, or output.

## Ephemeral behavior and limits

The writer and retriever share one in-process repository. All records disappear
when the process ends. There is no filesystem, database, legacy-memory access,
durable persistence, automatic learning, update/edit/delete, deduplication,
retention, expiration, locking, transaction, or concurrency guarantee.

Current prompt defenses label records as untrusted reference data but do not
provide advanced prompt-injection protection. Limits are character- and
record-based rather than token-based.

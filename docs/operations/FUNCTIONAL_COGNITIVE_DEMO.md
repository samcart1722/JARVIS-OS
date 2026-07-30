# Functional Cognitive Demo v1

## Purpose

This runbook operates Luxiom's local baseline-versus-memory comparison. It
demonstrates that the same user prompt can run once without memory context and
once with explicit, bounded, scoped reference data.

It demonstrates readiness gating, isolated runtime configuration, explicit
scope ownership, safe prompt labeling, and visible structured outcomes. It
does not demonstrate durable memory, learning, semantic search, ranking,
identity, HTTP scope integration, production security, or answer correctness.

## Prerequisites

- Use the repository virtual environment.
- Start Ollama locally.
- Install the model named by `OLLAMA_MODEL` before running the demo.
- Configure provider URLs, model, timeout, and prompt limits through existing
  Settings environment variables when the defaults are unsuitable.

The demo does not install Ollama, download models, or run `ollama pull`.

## PowerShell command

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_reasoning.py `
  --memory-scope "demo-session-1" `
  --memory-record "Luxiom separates its Cognitive Core from models." `
  --memory-record "HealthBridge is the first product planned on Luxiom." `
  "Explain what Luxiom is and mention its first product."
```

Use synthetic, non-sensitive references only. Command-line arguments may be
retained in PowerShell history, terminal logs, process inspection, or support
captures. Never pass secrets, personal or medical data, credentials, or
confidential business information.

## Approximate successful output

```text
Luxiom Functional Cognitive Demo v1
------------------------------------
Provider readiness: ready
Explicit memory scope: yes
Ephemeral scoped records: 2

BASELINE — WITHOUT MEMORY CONTEXT
Success: true
Response:
...

MEMORY-AWARE — WITH SCOPED MEMORY CONTEXT
Success: true
Response:
...
```

Generated responses vary by model and execution. The demo presents both
results and does not decide which is better.

## Controlled failure behavior

If Ollama is stopped, readiness reports `provider_unavailable`, prints its
canonical safe message, confirms that cognitive execution was not performed,
and exits with code 1.

If Ollama responds but the configured model is absent, readiness reports
`model_unavailable`, performs neither cognitive execution, and exits with code
1. Install or configure the model outside this demo; it never pulls a model.

If either cognitive execution returns a structured failure, its section prints
`Success: false`, the stable error code, and the safe message. No raw exception,
HTTP response, URL, internal prompt, or stack trace is intentionally printed.

Exit codes:

- `0`: readiness is ready and both cognitive outcomes are successful.
- `1`: readiness fails or either cognitive outcome fails.
- `2`: standard argparse behavior for missing or invalid CLI arguments.

## Ephemeral retrieval mechanism

The current scoped repository performs case-insensitive literal substring
matching. Only inside the CLI adapter, each synthetic record is wrapped as:

```text
[DEMO RETRIEVAL KEY]
<exact user prompt>

[USER-PROVIDED REFERENCE]
<exact user-provided record>
```

The wrapper makes the record addressable by the engine's normalized input. The
user payload is preserved without reinterpretation and no hidden facts are
added. The scope identifier is not serialized into the record or prompt. This
is not ranking, semantic search, embeddings, or persisted production memory.

Records exist only in the command's memory-aware Container. There is no write
operation, filesystem or database persistence, legacy-memory copy, Memory
Update, or permanent learning. A later invocation starts with new records.

## Current limits

- Retrieval is literal and intended only for controlled synthetic demo data.
- Memory is bounded by existing record-count and character settings, not token
  accounting.
- The safety label treats memory as untrusted reference data but is not
  advanced prompt-injection defense.
- There is no durable retention, deletion policy, authentication, identity,
  UI, installable distribution, legacy migration, or HTTP scope surface.
- Provider availability, model behavior, and generated wording can vary.

# Evidence-Bounded Reasoning Demo v1

## Purpose

This runbook compares the existing memory-aware reasoning path with the
evidence-bounded path using the same prompt, explicit ephemeral scope, and
synthetic records.

The grounded path asks the model for one strict JSON envelope, validates its
shape and record-number references, and renders a stable human response. This
improves discipline and auditability. It does not verify truth, prove that
every claim is supported, eliminate hallucinations, or provide complete
prompt-injection protection.

## Prerequisites

- Use the repository virtual environment.
- Start Ollama locally.
- Install the model named by `OLLAMA_MODEL`.
- Use only synthetic, non-sensitive demo records.

The command performs no model download, retry, fallback, file persistence,
database write, or HTTP API operation.

## PowerShell command

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_grounded_reasoning.py `
  --memory-scope "demo-session-1" `
  --memory-record "Luxiom separates its Cognitive Core from models." `
  --memory-record "HealthBridge is the first product planned on Luxiom." `
  "Explain what Luxiom is and mention its first product."
```

Command-line values may remain in shell history, logs, process inspection, or
support captures. Never use secrets, credentials, personal or medical data,
or confidential business information.

## Expected behavior

The runtime checks readiness exactly once. If ready, it executes the standard
memory-aware engine once and then the grounded engine once, with the exact
same prompt and explicit scope.

The standard section may contain free-form provider output. The grounded
section accepts only:

```json
{
  "status": "answered",
  "answer": "A response supported by the selected records.",
  "used_record_numbers": [1, 2]
}
```

or:

```json
{
  "status": "insufficient_evidence",
  "answer": "",
  "used_record_numbers": []
}
```

For `answered`, the visible response includes a stable footer such as
`Evidence used: scoped memory records 1, 2.` It does not expose the scope or
record contents. For `insufficient_evidence`, model wording is ignored and the
runtime displays `Insufficient scoped memory evidence to answer the current
request.`

Generated wording varies. Valid record numbers prove only that the response
used a well-formed envelope; they are not semantic fact verification.

## Controlled failures and exit codes

Malformed JSON, extra text, markdown fences, unexpected fields, invalid
types, duplicate numbers, or out-of-range references produce:

```text
Error code: grounded_response_protocol_invalid
Message: The reasoning provider returned an invalid evidence-bounded response.
```

The raw model response and stack trace are not displayed. There is no repair,
second model call, retry, or fallback to free text.

- `0`: readiness is ready and both outcomes succeed.
- `1`: readiness or either cognitive outcome fails.
- `2`: standard argparse failure for missing or invalid arguments.

## Current limits

- Records are selected deterministically by the existing count and character
  budgets, not token accounting or semantic ranking.
- The local retrieval wrapper uses literal query addressability and is not
  embeddings, RAG, or external retrieval.
- Memory and scope are ephemeral and local to the command.
- The parser validates syntax, structure, types, status, and references only.
- A model can still place an unsupported statement inside a valid envelope.
- The protocol is not a fact checker or complete prompt-injection defense.

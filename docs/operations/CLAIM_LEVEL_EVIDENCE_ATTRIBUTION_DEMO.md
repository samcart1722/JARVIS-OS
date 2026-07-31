# Claim-Level Evidence Attribution Demo v1

## Purpose

Sprint 18 extends Sprint 17's answer-level record references with a strict list
of claims and ordered record numbers for every claim. Global references alone
cannot show which assertion they are intended to support.

The demo compares the Sprint 17 evidence-bounded protocol with the Sprint 18
claim protocol using the same request, opaque scope, synthetic ephemeral
records, provider configuration, timeout, and limits. It demonstrates strict
structural attribution, controlled protocol failure, deterministic formatting,
one generation per execution, and no retry or fallback. It does **not** verify
truth, semantic support, factual fidelity, contradiction, or claim atomicity.

## Protocol

An answered envelope has exactly `status` and `claims`. Each claim has exactly
non-empty `text` and a non-empty, unique, positive, in-range
`used_record_numbers` list. An insufficient response is exactly:

```json
{"status":"insufficient_evidence","claims":[]}
```

Valid claims are rendered as numbered blocks followed by `Evidence used:
scoped memory records ...`. Insufficient evidence uses a fixed safe message.
Malformed JSON, Sprint 17 envelopes, missing references, and out-of-range
references become the existing `grounded_response_protocol_invalid` failure;
raw provider text is never returned.

## Run

Prerequisites are the existing virtual environment and an available configured
Ollama model. The records are synthetic and are not persisted.

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_claim_evidence_attribution.py `
  --memory-scope "demo-session-1" `
  --memory-record "Luxiom separa su Cognitive Core de los proveedores." `
  --memory-record "HealthBridge es el primer producto planificado sobre Luxiom." `
  "Explica qué es Luxiom y menciona su primer producto."
```

Output reports readiness, explicit-scope presence, record count, and both safe
outcomes. It never prints the actual scope, internal prompt, URL, raw JSON,
stack trace, or secrets. Exit code is `0` only when readiness and both outcomes
succeed, `1` for a safe readiness/execution failure, and argparse uses `2`.

## Residual risk and limitations

References are validated structurally, not semantically. A model can attach a
valid record number to an unsupported or compound claim. There is no fact
checker, second LLM, external search, contradiction detection, persistence,
ranking change, repair, retry, or fallback.

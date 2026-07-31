# Claim Evidence Support Verification Demo v1

Sprint 19 optionally adds one model-assisted support-classification call after
Sprint 18 produces a valid answered claim envelope. Each claim is sent with
only its exact cited bounded fragments; scope and uncited records are omitted.

Strict JSON verdicts drive an all-or-nothing gate. All supported claims retain
the exact Sprint 18 formatter output. Any unsupported claim returns the fixed
insufficient-evidence message. Malformed protocol fails closed. There is no
retry, repair, fallback, partial answer, rationale, or verification footer.

This classifies evidence support; it does not prove truth, correctness,
entailment, or factual accuracy. The same configured model performs generation
and verification, so false support and false rejection remain possible.

The verifier uses the exact deterministic bounded contents recomputed by the
same selector instance over the same immutable snapshot. There is no second
memory retrieval or repository access. This inherited Sprint 18 behavior is a
recomputation, not a claim of one-time selection.

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_claim_evidence_verification.py `
  --memory-scope "demo-session-1" `
  --memory-record "Luxiom separa su Cognitive Core de los proveedores." `
  --memory-record "HealthBridge es el primer producto planificado sobre Luxiom." `
  "Explica qué es Luxiom y menciona su primer producto."
```

The demo checks readiness once and runs Sprint 18 and Sprint 19 once each with
the same prompt, scope, ephemeral records, model, URLs, timeout, and evidence
limits. Nothing is persisted. Scope values, raw JSON/verifier output, URLs, and
stacks are not printed. Exit codes are `0` for both safe successes, `1` for
readiness/execution failure, and argparse `2` for invalid input.

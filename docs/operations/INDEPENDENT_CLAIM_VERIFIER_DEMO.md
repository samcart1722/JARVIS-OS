# Independent Claim Verifier Demo v1

Sprint 20 separates generation and verification roles through two independently
configured `OllamaClient` instances. Shared-client Sprint 19 remains the default;
independent mode is opt-in. `OLLAMA_VERIFIER_*` values are optional overrides;
when absent, primary endpoints, model, and timeout are reused by value in a
separate client instance. Calls remain sequential and there is no fallback.

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_independent_claim_verifier.py `
  --memory-scope "demo-session-1" `
  --memory-record "The approved project codename is ORBIT." `
  "Using only scoped memory, state the approved project codename."
```

`--verifier-model` may select an already installed verifier model. The demo
checks primary and verifier readiness before executing either engine, then runs
shared-client and independent-client modes once each with the same prompt,
scope, records, and primary configuration. It prints safe role/status labels,
never the scope value, URLs, raw protocol output, or stacks.
The primary probe represents the primary configuration common to both demo
scenarios; the verifier probe represents the independent client only.

Separate clients provide role and configuration separation only. Identical
models are allowed and distinct models may share architecture, training data,
vendor, family, and correlated errors. This does not prove truth, deterministic
entailment, semantic quality, or epistemic independence.

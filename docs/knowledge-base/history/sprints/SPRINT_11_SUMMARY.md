# Sprint 11 Summary — Provider Readiness and Demo Runtime v1

## Operational boundary

Added immutable `ProviderReadinessResult` and the small
`ProviderReadinessProbe.check()` contract outside the Cognitive Core. Stable
states are `ready`, `provider_unavailable`, `model_unavailable`, and
`invalid_response`; messages are canonical and safe.

`OllamaReadinessProbe` uses one non-generative model-list operation. Ollama
documents `GET /api/tags` as listing available models. Because existing
`OLLAMA_BASE_URL` stores the complete `/api/generate` endpoint,
`OLLAMA_MODELS_URL` was added with default
`http://localhost:11434/api/tags` instead of fragile string replacement.

The probe, client, provider, Container, and engine remain inert during
construction. No automatic readiness, retry, fallback, generate, pull, model
load, warmup, endpoint, or public API change was introduced.

## Demo runtime

`ReasoningDemoRuntime` receives enablement, the readiness contract, and the
already-composed engine. Disabled reasoning causes no network or cognitive
execution. Enabled reasoning checks once; only `ready` reaches
`CognitiveEngine.process`. Existing `CognitiveOutcome` makes cognitive failure
distinct from operational readiness failure.

The thin adapter is invoked with:

```powershell
.\.venv\Scripts\python.exe .\scripts\demo_reasoning.py "Explain Luxiom"
```

Tests use mocks only and require no Ollama or network. They cover safe result
invariants, one-operation discovery, transport/malformed-response mapping,
inert composition, demo gating, outcome preservation, no fallback, thin CLI,
and Core/API boundaries.

Real debt remains the pytest cache warning and historically imprecise
`OLLAMA_BASE_URL` name. Multi-provider policy, retries, health HTTP, metrics,
streaming, model lifecycle, memory, evidence, tools, files, and web remain
deliberately deferred. Explicit boundary lists and runtime documents require
ongoing governance maintenance.

No dependency, commit, push, tag, merge, or staging action was added or
performed.

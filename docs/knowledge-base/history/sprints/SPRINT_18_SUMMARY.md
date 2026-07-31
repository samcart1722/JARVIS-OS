# Sprint 18 Summary — Claim-Level Evidence Attribution v1

Sprint 18 added an opt-in claim attribution protocol on top of explicit Sprint
17 grounding. Immutable claim/envelope models, a strict standard-library JSON
parser, deterministic formatter, prompt policy, and provider decorator share
the existing bounded evidence selector. Invalid protocol reuses
`grounded_response_protocol_invalid`; insufficient evidence remains safe.

The composition root selects exactly one path: historical when grounding is
off, Sprint 17 when grounding is on and claim attribution is off, or Sprint 18
when both flags are on. Missing/empty snapshots preserve exact pass-through.
No API, `ReasoningResult`, or `CognitiveOutcome` contract changed.

The operational demo compares Sprint 17 and Sprint 18 with isolated in-memory
repositories and one readiness check. It makes no semantic-verification claim.

Deferred work includes semantic verification, fact checking, contradiction
detection, claim atomicity, durable scoped persistence, delete/update,
migration and identity, HTTP exposure, ranking, advanced prompt defense,
tokenization, retention, and concurrency. Inherited debt remains: global
legacy memory, legacy data without ownership, and imprecise
`OLLAMA_BASE_URL` naming.

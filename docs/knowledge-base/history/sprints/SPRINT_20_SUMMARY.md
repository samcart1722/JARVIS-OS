# Sprint 20 Summary — Independent Claim Verification Provider v1

Sprint 20 adds an opt-in independent verifier client with separately configured
optional Ollama model, endpoint, and timeout overrides. Missing overrides reuse
the corresponding primary values by value while still creating a distinct
client instance. Default Sprint 19 behavior reuses the primary client exactly.
Independent mode is sequential, with no retry or fallback. Container
construction remains inert.

This completes role/configuration separation, not factual truth or guaranteed
independence. Vendor/family diversity policy, external sources, deterministic
entailment, confidence, contradictions, partial filtering, durable audit, HTTP,
and human review remain deferred. Separate clients may use identical or
correlated models. Inherited global memory, ownership, historical URL naming,
and deterministic evidence-selection recomputation remain debt.

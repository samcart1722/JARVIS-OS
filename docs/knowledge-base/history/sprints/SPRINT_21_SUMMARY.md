# Sprint 21 Summary

Sprint 21 implements the first typed local-first vertical: explicit actor and
workspace values, deny-by-default permissions, a generic structured-list
capability, an in-memory workspace/list-scoped repository, deterministic local
results, and an offline operational demo. `Container` composes the route once;
`CognitiveEngine`, public API models, ReasoningResult, CognitiveOutcome and the
Sprint 17–20 verification contracts remain unchanged.

Duplicate policy trims surrounding whitespace, compares by case-folding,
preserves the first accepted display form and insertion order, and reports new
and existing items separately. Permission is evaluated before repository
access. Tests spy on the model boundary to establish zero calls.

Limitations: no durable persistence, authentication, natural-language intent
extraction, broad local knowledge retrieval, external policy engine, automatic
learning, voice, mobile or wearable interface. ADR governance remains Draft;
no ADR was represented as approved.

The resolver is composed in `Container` but is not integrated into
`CognitiveEngine.process` or the public API. Unsupported typed intents return
`not_handled`; no automatic bridge selects the separately available historical
reasoning route. At its review checkpoint Sprint 21 was uncommitted; it was
subsequently released at `8c0330b`, tag `sprint-21-complete`.

# Sprint 23 Summary

Sprint 23 implements an explicit application-level coordinator for already-
typed local intents. It calls `LocalFirstResolver` exactly once. Handled local
success or controlled failure is terminal and preserved without error-code
reinterpretation. Only `not_handled`, explicit fallback authorization, and
valid non-blank cognitive input may call the existing cognitive processor.

Immutable request, authorization, route, safe-insufficiency reason, and result
types enforce mutually exclusive local and cognitive payloads. The coordinator
depends on a `CognitiveProcessor` Protocol and imports no persistence,
framework, network, provider, or operational module.

`Container` composes one coordinator from its existing resolver and engine.
Public HTTP still calls `CognitiveEngine` directly. No natural-language parser,
setting, schema change, database, authentication, or model fallback was added.

The opt-in demo uses the real in-memory Container with reasoning disabled and
shows local, safe-insufficiency, and deterministic cognitive routes with
route-contract cognitive counts `0`, `0`, and `1`; the unit test independently
observes one actual processor call. All remote-call counts are zero.

Sprint 22 is released at `9dcb36b`, tag `sprint-22-complete`. Sprint 23 remains
implemented only in `feat/sprint-23-local-first-cognitive-routing`, uncommitted,
unmerged, and untagged. Constitution and ADR standard remain Draft; no approved
ADR is claimed. Implementation validation and independent review both passed
591 tests; the independent review completed in 4.30 seconds. Ruff and
`git diff --check` were clean.

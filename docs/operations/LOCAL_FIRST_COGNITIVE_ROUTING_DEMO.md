# Explicit Local-First Cognitive Routing Demo

Run the opt-in deterministic demo without a database or network:

```powershell
& .\.venv\Scripts\python.exe -m scripts.demo_local_first_cognitive_routing
```

The thin CLI creates the real in-memory `Container` with reasoning disabled and
passes its composed coordinator to the operations runtime. The runtime shows:

1. A handled typed list command selects `local`; cognitive calls remain zero.
2. An unsupported intent without authorization selects `safe_insufficiency`;
   cognitive calls remain zero.
3. An unsupported intent with explicit authorization and valid input selects
   the existing deterministic cognitive path exactly once.

The cognitive route does not imply model use. This demo reports zero model,
external, readiness, and network calls. It creates no database and does not
exercise or change public HTTP.

The displayed cognitive values `0`, `0`, and `1` are route-contract counts:
they identify which coordinated result selected the cognitive route. They are
not a production invocation counter. The runtime unit test separately wraps the
cognitive processor with a mock and verifies one actual `process` call.

There is no natural-language local-intent parser and no automatic fallback in
`CognitiveEngine` or the API. Authentication, RBAC, semantic retrieval,
knowledge prompt integration, synchronization, encryption, and external-access
policy remain deferred.

# Sprint 8 Summary — Deterministic Reasoning Selection Policy v1

## Contract and implementation

`ReasoningSelectionPolicy` defines:

`select_capability(context: CognitiveContext) -> str`

`DeterministicReasoningSelectionPolicy` receives immutable
`reasoning_enabled: bool`. `False` returns the official
`NORMALIZED_INPUT_CAPABILITY_ID`; `True` returns the official
`REASONING_CAPABILITY_ID`.

The implementation does not import Settings, Ollama, providers, registry, HTTP,
or I/O. It does not inspect prompt text, domain, complexity, keywords, provider
availability, or model identity.

## Configuration and composition

`Settings.REASONING_ENABLED` defaults to `False`, supports standard Pydantic
environment override, and is documented safely as
`REASONING_ENABLED=false` in `.env.example`.

`Container` constructs the policy from Settings, injects it into
`DefaultSpecialist`, and injects that specialist into `SpecialistRouter`.
Both `normalized_input` and `reasoning` remain registered regardless of the
flag. Composition performs no network I/O.

## Specialist and runtime

The specialist contract now plans from `CognitiveContext`.
`DefaultSpecialist` calls the policy exactly once, preserves its one-step plan
shape and description, and uses the returned identifier unchanged. It knows
neither Settings nor providers.

Disabled/default:

`false → normalized_input → existing deterministic response`

Enabled:

`true → reasoning → ReasoningCapability → ReasoningStage →
ReasoningProvider → real provider output`

Tests use a controlled provider boundary. Empty output remains a controlled
failure; unexpected exceptions propagate. No fallback to normalized input,
retry, health check, heuristic, or prompt analysis exists. Enabling the flag
does not assert that Ollama is operational.

## Verification and debt

Baseline: **45 passed, 1 warning in 1.05s**; Ruff passed and
`git diff --check` was clean.

Final: **63 passed, 1 warning in 1.41s** with `DEBUG=true`. Ollama and network
are not required. The warning is the pre-existing pytest cache-path issue.

Resolved: explicit deterministic reasoning selection and composition.

Pending: provider availability, provider selection, operational failure policy,
and all previously deferred memory, evidence, tools, web, files, retries,
streaming, and domain-specialist work.

No commit, push, tag, merge, or staging action was performed.

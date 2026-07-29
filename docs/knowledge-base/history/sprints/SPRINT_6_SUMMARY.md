# Sprint 6 Summary — Reasoning Capability v1

## Implemented

- Added the provider-independent logical identifier `reasoning`.
- Added `ReasoningCapability`, which translates canonical reasoning results
  into `CapabilityResult`.
- Registered both `normalized_input` and `reasoning` in the shared
  `CapabilityRegistry`.
- Composed the existing `OllamaProvider`, `ReasoningStage`, and
  `ReasoningCapability` from `Container`.

## Reuse decision

`ReasoningStage` was reused because it already provides the single canonical
invocation:

`CognitiveContext → ReasoningProvider.generate → ReasoningResult`

Calling the provider directly from the capability would duplicate this
boundary. The capability depends on the stage, while the stage depends on the
existing `ReasoningProvider` protocol. `OllamaProvider` is not imported or
constructed by `ReasoningCapability`.

## Result semantics

- Non-empty provider text produces successful capability output.
- Empty or whitespace-only text produces a controlled failure with the safe
  error `Reasoning provider returned no output.`
- Unexpected exceptions propagate through the executor and retain existing
  HTTP 500 behavior.
- The provider/stage is invoked exactly once and context is not mutated.

Tests use local fake providers. No Ollama process, model, network, or external
service is required.

## Composition and public policy

Constructing `OllamaProvider` only initializes the existing client fields and
does not call the network. A plan that explicitly requests `reasoning` resolves
and executes the capability through the shared runtime.

`DefaultSpecialist` deliberately continues requesting `normalized_input`.
Therefore `POST /brain/think` preserves its deterministic HTTP 200 response and
does not activate Ollama. Model-backed reasoning is available but not yet the
approved default public policy.

## Verification and pending work

Baseline: **24 passed, 1 warning in 0.86s**.

Final: **34 passed, 1 warning in 1.10s**. The warning remains the pre-existing
pytest cache-path warning.

Pending work includes externalizing Ollama URL/model/timeout, deciding provider
selection and public activation policy, and all previously deferred memory,
evidence, tools, fallback, retry, streaming, and domain-specialist work.

No commit was created by Sprint 6.

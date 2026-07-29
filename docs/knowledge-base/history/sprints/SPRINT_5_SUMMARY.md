# Sprint 5 Summary — Capability Runtime v1

## Implemented

- Added immutable `PlanStep.capability_id` with a compatibility default.
- Added a direct `CapabilityRegistry` with duplicate and missing-identifier
  errors.
- Changed `CapabilityExecutor.execute` to receive `CognitiveContext` and
  `Plan`, invoke capabilities sequentially, and aggregate `CapabilityResult`
  into `ExecutionResult`.
- Added aggregated execution metadata.
- Updated `ResponseStage` to expose real outputs on success.

## Deterministic bootstrap capability

`NormalizedInputCapability` returns `CognitiveContext.normalized_input`.
Its stable logical identifier is `normalized_input`, defined separately from
the implementation. It uses no model, network, files, memory, or external
service and does not perform reasoning or intelligence.

`DefaultSpecialist` requests only that identifier. `Container` constructs the
implementation and registry, registers it explicitly, and injects the registry
into the executor.

## Execution policy

- Sequential execution with plan order preserved.
- A step is completed only after `CapabilityResult.success=True`.
- Controlled failure is fail-fast and retains earlier completed steps,
  outputs, and metadata.
- Missing capability returns a failed `ExecutionResult` and completes no
  affected step.
- Unexpected exceptions propagate to the existing HTTP 500 boundary.
- An empty plan succeeds with no work or output.

## Public result

For `POST /brain/think?prompt=Return+this+deterministic+input`, the response is:

`{"input":"Return this deterministic input","response":"Return this deterministic input"}`

The query parameter, response fields, and HTTP 200 success contract remain
unchanged. A controlled capability failure returns the safe text
`Plan execution failed.` and is not represented as successful execution.

## Verification and pending work

Baseline: **12 passed, 1 warning in 0.96s**.

Final: **24 passed, 1 warning in 0.85s**. The warning is the pre-existing
pytest cache-path warning. Capability runtime and public-route tests require no
Ollama, model, network, or other external service.

Pending work includes useful concrete capabilities, reasoning, memory update,
evidence, tools, richer response contracts, retries, replanning, parallelism,
and domain specialists. None was implemented in this sprint.

No commit was created by Sprint 5.

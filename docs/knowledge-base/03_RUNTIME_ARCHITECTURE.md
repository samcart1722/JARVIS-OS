# Runtime Architecture

This document describes only the code executed at commit `74637ab`.

## Public path and flow

```text
POST /brain/think?prompt=...
        |
        v
app.api.routes.brain:think
        |
        v
module-level Container instance -> CognitiveEngine
        |
        v
user_input
  -> Goal + CognitiveContext
  -> DefaultGoalClassifier -> Domain.UNKNOWN
  -> SpecialistRouter -> DefaultSpecialist
  -> Plan(one PlanStep requiring "normalized_input")
  -> CapabilityExecutor(context, plan)
  -> CapabilityRegistry -> NormalizedInputCapability
  -> CapabilityResult -> ExecutionResult
  -> ResponseStage -> normalized request input
```

The public HTTP input is a `prompt` query parameter and the HTTP output is a
JSON object containing `input` and string `response`. The current Core entry
point is `CognitiveEngine.process(user_input: str) -> str`.

## Stage responsibilities

| Stage | Runtime responsibility |
|---|---|
| `CognitiveEngine` | Owns sequencing; directly constructs goal/context and coordinates dependencies. |
| `DefaultGoalClassifier` | Discards context and returns the fallback domain. |
| `SpecialistRouter` | Resolves all domains to the same default specialist. |
| `DefaultSpecialist` | Builds a provisional one-step plan requesting `normalized_input`. |
| `CapabilityRegistry` | Resolves logical identifiers to implementations composed by `Container`. |
| `CapabilityExecutor` | Runs steps sequentially, passes context and step to capabilities, aggregates results, and fails fast. |
| `NormalizedInputCapability` | Returns normalized context input deterministically; it performs no reasoning. |
| `ResponseStage` | Returns aggregated output on success or safe fixed failure text. |

## Dependencies and composition

`app/core/container.py` is the Composition Root. `_build_reasoning()` constructs
and registers `NormalizedInputCapability`, constructs `CapabilityExecutor`
with the registry, then injects the executor and other stages into
`CognitiveEngine`.
The module creates a module-level `container`; the FastAPI route consumes its
`cognitive_engine` without rebuilding dependencies. `_build_memory()` separately composes
the cognitive memory pipeline and a `LegacyMemoryAdapter`.

## Core boundaries

The active Core path is primarily `app/cognition`, with composition in
`app/core/container.py`. FastAPI is outside that Core. Legacy `app/brain` is
also outside the Core and no longer participates in the public cognitive path.
The engine depends on classifier/specialist contracts and concrete executor and
response-stage classes. Plans reference only stable logical capability
identifiers. No product-specific HealthBridge logic appears in this path.

## Execution policy v1

Execution is sequential and ordered. A step is completed only after its
capability returns `success=True`. Outputs and metadata are aggregated. Missing
capabilities produce a failed `ExecutionResult`; controlled failure preserves
prior successful work and stops the plan. Unexpected exceptions propagate to
the existing HTTP 500 handling. An empty plan succeeds with no completed work
or output.

## Documented versus executable lifecycle

The normative Cognitive Lifecycle includes Task Builder, Task, Workspace,
capabilities, evidence, reasoning/tools during execution, replanning, and Memory
Update. Sprint 5 activates one deterministic capability but still has no Task
Builder, evidence model, reasoning/tool execution, replanning, or memory update.

`InputStage`, `ContextStage`, and provider-backed `ReasoningStage` exist from
Sprint 1 but are bypassed by the current engine implementation. They must not be
described as active stages.

## Legacy and alternative modules

- `app/brain` remains in the repository but its `Brain` and `Orchestrator`
  classes are disconnected from the public cognitive operation.
- `app/memory`, `app/reasoning`, `app/context`, `app/prompt`, and related
  managers predate or sit outside the current `app/cognition` boundary.
- `app/tests` contains an older test suite not collected by the configured
  pytest `testpaths`.
- The memory pipeline under `app/cognition/memory` is composed but not connected
  to `CognitiveEngine.process`.

These paths are recorded, not deprecated or removed by this recovery task.

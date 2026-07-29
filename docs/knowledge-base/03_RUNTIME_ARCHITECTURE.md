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
  -> Plan(one descriptive PlanStep)
  -> CapabilityExecutor -> ExecutionResult
  -> ResponseStage -> "Plan executed successfully."
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
| `DefaultSpecialist` | Builds a one-step high-level plan from the goal. |
| `CapabilityExecutor` | Marks descriptions completed; it does not dispatch capabilities or tools. |
| `ResponseStage` | Maps execution success to a fixed public string. |

## Dependencies and composition

`app/core/container.py` is the Composition Root. `_build_reasoning()` constructs
`DefaultGoalClassifier`, `SpecialistRouter`, `CapabilityExecutor`, and
`ResponseStage`, injects them into `CognitiveEngine`, and exposes the engine.
The module creates a module-level `container`; the FastAPI route consumes its
`cognitive_engine` without rebuilding dependencies. `_build_memory()` separately composes
the cognitive memory pipeline and a `LegacyMemoryAdapter`.

## Core boundaries

The active Core path is primarily `app/cognition`, with composition in
`app/core/container.py`. FastAPI is outside that Core. Legacy `app/brain` is
also outside the Core and no longer participates in the public cognitive path.
The engine depends on classifier/specialist contracts and concrete executor and
response-stage classes. No product-specific HealthBridge logic appears in this
path.

## Documented versus executable lifecycle

The normative Cognitive Lifecycle includes Task Builder, Task, Workspace,
capabilities, evidence, reasoning/tools during execution, replanning, and Memory
Update. These are not active in the Sprint 3 path. The runtime instead creates
`Goal` and `CognitiveContext` directly, has no Task Builder, invokes no
capability, produces no evidence, performs no memory update, and returns a
fixed response.

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

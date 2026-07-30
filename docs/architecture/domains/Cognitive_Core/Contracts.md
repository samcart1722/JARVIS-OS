# Cognitive Core — Active Contracts

Status: **Executable baseline v1**
Signatures reflect Sprint 11 code based on checkpoint `f843842`.

## Orchestration contracts

### CognitiveEngine

```python
process(user_input: str) -> CognitiveOutcome
```

Creates one `Goal` and `CognitiveContext`, classifies the context, resolves a
specialist, requests a plan, executes it with the same context, and passes the
result to `ResponseStage`. It does not resolve or execute capabilities itself.

### GoalClassifier

```python
classify(context: CognitiveContext) -> Domain
```

The active implementation returns `Domain.UNKNOWN` for every context.

### SpecialistRouter

```python
route(domain: Domain) -> Specialist
```

The active router maps every domain to one injected `DefaultSpecialist`.

### Specialist

```python
can_handle(goal: Goal) -> bool
create_plan(context: CognitiveContext) -> Plan
```

Specialists plan; they do not execute capabilities or infrastructure.

## Selection contract

### ReasoningSelectionPolicy

```python
select_capability(context: CognitiveContext) -> str
```

The result is a logical capability identifier placed unchanged in a
`PlanStep`. The active deterministic implementation returns
`NORMALIZED_INPUT_CAPABILITY_ID` when disabled and `REASONING_CAPABILITY_ID`
when enabled.

Invariants: one call per default plan, no context mutation, no I/O, no provider
knowledge, no registry lookup, no prompt heuristics, and no fallback.

## Planning contracts

```python
Goal(description: str)
Plan(steps: tuple[PlanStep, ...])
PlanStep(id: str, description: str, capability_id: str = "")
```

`Plan.steps` order is execution order. `capability_id` names a logical
capability; it never stores a capability instance. A step becomes completed
only after its resolved capability returns `success=True`.

The empty-string default on `capability_id` is compatibility behavior; if
executed without a registration it follows missing-capability failure
semantics.

## Capability contracts

### Capability

```python
execute(
    context: CognitiveContext,
    step: PlanStep,
) -> CapabilityResult
```

### CapabilityRegistry

```python
register(capability_id: str, capability: Capability) -> None
get(capability_id: str) -> Capability
```

Duplicate registration raises `CapabilityAlreadyRegisteredError`. Missing
lookup raises `CapabilityNotFoundError`; the executor translates that known
condition into a failed `ExecutionResult`.

### CapabilityExecutor

```python
execute(context: CognitiveContext, plan: Plan) -> ExecutionResult
```

Execution is sequential, ordered, and fail-fast:

- successful outputs and copied metadata are accumulated;
- a step is recorded completed only after capability success;
- `success=False` stops execution and preserves prior completed work/output;
- a missing capability fails without completing the affected step;
- unexpected capability exceptions propagate;
- an empty plan succeeds with no completed steps or output;
- executor result state is local to each call.

### Result models

```python
CapabilityResult(
    success: bool,
    outputs: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
    error_code: str | None = None,
    metadata: dict[str, object] = {},
)

ExecutionResult(
    success: bool,
    completed_steps: tuple[str, ...],
    outputs: tuple[str, ...] = (),
    errors: tuple[str, ...] = (),
    error_code: str | None = None,
    metadata: tuple[dict[str, object], ...] = (),
)
```

The displayed capability metadata default is conceptual; implementation uses a
per-instance factory. Known failures carry `capability_not_found`,
`capability_execution_failed`, or `empty_capability_output`. Internal `errors`
remain available to runtime tests but are never copied to the public response.

## Reasoning contracts

### ReasoningProvider

```python
generate(context: CognitiveContext) -> ReasoningResult
```

### ReasoningStage

```python
process(context: CognitiveContext) -> ReasoningResult
```

The stage invokes its injected provider once.

### ReasoningCapability

Uses `ReasoningStage` once for an execution. A non-empty provider response
becomes one successful output. Empty or whitespace-only response becomes a
controlled failure with `Reasoning provider returned no output.` Unexpected
exceptions propagate. The capability does not know the concrete provider.

```python
ReasoningResult(response: str)
```

The result model itself does not enforce non-empty text; that policy belongs to
`ReasoningCapability`.

## Response contract

```python
ResponseStage.process(execution_result: ExecutionResult) -> CognitiveOutcome
```

- Success joins real outputs and creates `success=True`, a non-empty
  `response`, and no error.
- Controlled failure creates `success=False`, `response=None`, and a
  `CognitiveError`.
- It never parses internal error messages and never knows FastAPI or HTTP.

`CognitiveOutcome` rejects success with an error, success without useful text,
failure without an error, and failure with a cognitive response. The HTTP
boundary maps `capability_not_found` to 500 and the two execution/output
failures to 503. Unexpected exceptions continue through FastAPI's existing 500
handling.

## Composition contracts

`Settings -> Container` is the operational boundary. `Container`:

- builds an inert configured `OllamaClient`;
- injects it into `OllamaProvider`;
- injects the provider into `ReasoningStage`;
- injects the stage into `ReasoningCapability`;
- translates `REASONING_ENABLED` into the deterministic selection policy;
- injects the policy into `DefaultSpecialist`;
- registers both active capabilities;
- builds the executor and engine.

Construction performs no network call. `REASONING_ENABLED=true` selects
reasoning; it does not prove Ollama/model availability.

## Verified invariants

- The registry contains `normalized_input` and `reasoning`.
- Default configuration selects normalized input and does not call the provider.
- Explicit enablement selects reasoning.
- Policy output depends only on immutable boolean enablement.
- Policy does not mutate context or know providers.
- API uses the composed engine and does not construct concrete infrastructure.
- Provider-backed output reaches `CapabilityResult`, `ExecutionResult`, and
  `ResponseStage`.
- There is no silent fallback from reasoning to normalized input.
- Container/client/provider construction performs no network I/O.

## Operational readiness contracts

Outside the Cognitive Core,
`ProviderReadinessProbe.check() -> ProviderReadinessResult`. The immutable
result has a stable `status`, matching `ready` boolean, and canonical safe
`message`. States are `ready`, `provider_unavailable`, `model_unavailable`,
and `invalid_response`; contradictory state is rejected.

The Ollama implementation performs exactly one non-generative model-list
operation and never generates, downloads, loads, warms, retries, or falls
back. The demo checks enablement first, calls readiness once only when enabled,
and invokes the composed engine only when ready while preserving the existing
`CognitiveOutcome`.

## Scoped memory persistence contract

Sprint 12 defines an inactive read-only contract:

```python
ScopedMemoryRepository.search(
    scope: MemoryScope,
    query: str,
) -> tuple[ScopedMemoryRecord, ...]
```

Scope and content are required, non-blank, immutable values. The in-memory
implementation accepts an immutable tuple of initial records, selects the
requested scope before a case-insensitive literal substring match, and
preserves constructor order. There is no unscoped overload, `search_all`, or
write method.

## Memory context integration contracts

```python
MemoryContextRetriever.retrieve(
    scope: MemoryScope,
    query: str,
) -> MemorySnapshot

CognitiveEngine.process(
    user_input: str,
    *,
    memory_scope: MemoryScope | None = None,
) -> CognitiveOutcome
```

`MemorySnapshot(scope, records)` is frozen and rejects cross-scope records.
`None` in `CognitiveContext.memory_snapshot` means retrieval did not execute;
an empty snapshot means it executed with no matches.

Disabled retrieval or absent scope performs no call. Enabled retrieval with
scope calls once using normalized input, verifies the returned scope, replaces
the immutable context, and only then classifies. Unexpected errors propagate.
Enabling retrieval without an injected retriever is rejected at construction.

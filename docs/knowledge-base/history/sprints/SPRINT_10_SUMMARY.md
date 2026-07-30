# Sprint 10 Summary — Structured Cognitive Outcome v1

## Alcance completado

The Core now returns a validated `CognitiveOutcome` containing either a
non-empty response or a `CognitiveError`. Stable codes are
`capability_not_found`, `capability_execution_failed`, and
`empty_capability_output`. The executor assigns or preserves these codes at the
point where the failure is known; no message-string classification exists.

`ResponseStage` converts `ExecutionResult` to the domain outcome and knows
neither FastAPI nor HTTP. `CognitiveEngine.process` has one clear
`CognitiveOutcome` return type. The API owns separate Pydantic response models
and maps success to HTTP 200, missing capability to 500, and controlled
execution/empty-output failures to 503. Public failures contain safe canonical
messages and never raw provider or execution details. Unexpected exceptions
continue through the existing HTTP 500 behavior.

The successful default path preserves the original deterministic output and
does not call Ollama. Explicit reasoning with a controlled provider preserves
its real output. No fallback, retry, provider/configuration change, network
requirement, dependency, endpoint, middleware, or broad refactor was added.

## Pruebas

Baseline: **70 passed, 1 warning in 1.69s** with `DEBUG=true`; Ruff and
`git diff --check` passed. Final: **86 passed, 1 warning in 1.25s**; Ruff and
`git diff --check` passed. The persistent warning is the known local pytest
cache-path issue.

Coverage includes outcome invariants, centralized infrastructure-neutral
codes, executor propagation/fail-fast behavior, response mapping, engine
return type, deterministic and controlled reasoning paths, safe API success
and failure representations, unexpected HTTP 500 behavior, and AST boundaries.

## Roadmap deliberadamente diferido

Provider availability, health/readiness, retries, fallback, streaming,
evidence, memory update, tools, files, web, domain specialists, richer
response content, and global error middleware remain outside this sprint.

## Deuda heredada restante

Provisional classification/routing/planning, inactive memory and input/context
stages, legacy parallel modules, identity inconsistency, explicit architecture
test scope maintenance, and local pytest cache hygiene remain unchanged.

## Deuda nueva introducida

None known. The implementation uses existing dataclasses, Pydantic, FastAPI,
and standard-library AST tests; no dependency or compatibility shim was added.

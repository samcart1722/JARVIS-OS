# Sprint 4 Summary — Canonical Cognitive Runtime

## Implemented

- Changed `POST /brain/think?prompt=...` to call
  `container.cognitive_engine.process(prompt)` directly.
- Preserved the public query parameter, response fields, success status, and
  existing FastAPI error behavior.
- Added behavioral tests for the HTTP boundary, engine failure, and Container
  composition.

## Integrated

The public runtime is now:

`HTTP route → Container.cognitive_engine → Goal/CognitiveContext → classifier
→ specialist → plan → executor → ResponseStage → HTTP response`

The route does not construct classifier, router, specialist, executor, or
response-stage dependencies.

## Legacy delimited

`app/brain/Brain` and `app/brain/Orchestrator` remain in the repository but no
longer participate in the public cognitive operation. They were not deleted:
the sprint established disconnection, while broad deletion of historical code
was neither required nor sufficiently supported by repository-wide evidence.

Historical `app/reasoning`, `app/context`, `app/memory`, handlers, tools, and
the excluded `app/tests` suite remain outside this migration.

## Pending

- Memory Update and integration of cognitive memory.
- Concrete capabilities, registry/resolver, tools, models, web, files, vision,
  voice, automation, and product-specific integrations.
- Classification and specialist behavior beyond provisional fallbacks.
- Consumer-by-consumer evaluation of remaining historical modules.
- The pre-existing pytest cache warning and excluded legacy test suite.

## Verification

Baseline: **9 passed, 1 warning in 0.14s**.

Final: **12 passed, 1 warning**. The warning is the pre-existing inability to
write `.pytest_cache`; no Ollama or external service is required.

No commit was created by Sprint 4.

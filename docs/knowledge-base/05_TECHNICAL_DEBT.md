# Technical Debt

## Sprint 11 classification

### Technical debt

- Local pytest cache writes can emit a permission/path warning.
- Historical `OLLAMA_BASE_URL` denotes a complete generation endpoint; its
  imprecise name is retained for compatibility.

### Deliberately deferred roadmap

Provider registries, multi-provider selection, retries, circuit breakers,
automatic health endpoints, metrics, model download/warmup, streaming, memory,
evidence, tools, files, and web are future scope, not current defects.

### Governance maintenance

Keep explicit AST boundary lists and operational documentation aligned when
active files change.

## Sprint 12 classification

### Inherited technical limitation

The global memory repository and legacy records lack ownership and cannot be
exposed through the scoped boundary.

### Deliberately deferred roadmap

Legacy migration, writes, durable persistence, engine/Container integration,
retrieval snapshots, and safe memory use in model prompts are deferred.

### Governance maintenance

When scoped memory becomes active, extend enforcement to retrieval,
composition, context propagation, and public-boundary exclusions.

## Sprint 13 classification

### Technical debt

The global legacy repository and unowned legacy records remain incompatible
with scoped retrieval. The historical Ollama generation URL setting retains
its imprecise base-URL name.

### Deliberately deferred roadmap

Durable persistence, writes, Memory Update, legacy migration, authenticated
identity/scope transport, memory selection policy, stored prompt-injection
defense, safe prompt incorporation, retention, and deletion remain deferred.

### Governance maintenance

Keep explicit AST lists synchronized as new memory consumers become active.

Only inspected, evidenced items are included. This register does not authorize
fixing them.

| ID | Description and evidence | Impact | Priority | Recommended timing | Do not do yet |
|---|---|---|---|---|---|
| TD-001 | Resolved in Sprint 5: `CapabilityExecutor.execute` receives `CognitiveContext` and `Plan`, then passes context and step to the selected capability. | Concrete capabilities can execute against request context. | Resolved | Sprint 5 | Preserve this boundary when adding capabilities. |
| TD-002 | `DefaultGoalClassifier.classify` deletes context and always returns `Domain.UNKNOWN`. | Domain routing is only a fallback demonstration. | High | Before domain-specific specialist selection. | Do not embed client rules directly in the classifier. |
| TD-003 | `SpecialistRouter` maps every `Domain` to one `DefaultSpecialist`; that specialist creates one descriptive step. | Planning is structurally integrated but not meaningful. | High | With formally scoped specialist/planning work. | Do not add domain logic to `CognitiveEngine`. |
| TD-004 | Resolved for v1 in Sprint 5: a direct registry and deterministic normalized-input capability are composed and invoked. | Execution now reflects a real `CapabilityResult`; broader useful capabilities remain absent. | Resolved for v1 | Sprint 5 | Do not describe the bootstrap capability as reasoning or intelligence. |
| TD-005 | Cognitive memory is composed in `Container` but not called by `CognitiveEngine.process`; no Memory Update exists in the active flow. | Runtime is shorter than the Cognitive Lifecycle and does not retain task results. | High | When memory integration is formally selected. | Do not couple the engine directly to memory persistence. |
| TD-006 | Legacy/parallel code remains under `app/brain`, `app/memory`, `app/reasoning`, `app/context`, and other managers. Sprint 4 removed `app/brain` from the HTTP cognitive path, but did not prove every historical module safe to delete. | Multiple mental models still obscure ownership outside the canonical public path. | Medium | Map remaining consumers before selective removal. | Do not delete or rename legacy modules without consumer and test evidence. |
| TD-007 | `pyproject.toml` collects only `tests/`; numerous tests under `app/tests/` are not in the verified 9-test run. | Older behavior may be unverified or depend on undeclared/external services. | High | Before relying on legacy modules or changing test layout. | Do not claim all repository tests pass based on the configured suite. |
| TD-008 | Resolved for the active v1 runtime in Sprint 9: Components, Contracts, and Dependency Rules now document executable reality and have minimum completeness tests. Other Blueprint/standards shells retain their original status. | Active Core boundaries are reviewable without promoting unrelated drafts. | Resolved for active v1 | Sprint 9 | Do not treat the baseline as proof of future lifecycle stages. |
| TD-018 | Architecture import tests intentionally cover a short explicit list of active files and exclude legacy modules. | New active files require conscious addition to the governance scope. | Medium | Whenever the canonical runtime expands. | Do not replace the explicit baseline with indiscriminate repository scanning. |
| TD-009 | `Container` has `_build_context`, `_build_prompt`, `_build_models`, `_build_reflection`, `_build_learning`, `_build_tools`, `_build_vision`, and `_build_speech` methods containing `pass`. | Composition advertises domains not actually built. | Medium | As each domain receives approved scope. | Do not present scaffolds as integrated functionality. |
| TD-010 | `Settings` hard-codes JARVIS-OS name/version, development environment, and `DEBUG=True`; `pyproject.toml` and README also retain old identity. | Runtime/public metadata conflicts with Luxiom and defaults may be unsuitable outside development. | Medium | Dedicated configuration/identity decision. | Do not perform broad rebranding in this task. |
| TD-011 | Partially resolved in Sprint 6: `ReasoningStage` is reused by registered `ReasoningCapability`; `InputStage` and `ContextStage` remain bypassed. | The provider boundary is active on demand, while earlier input/context abstractions remain isolated. | Medium | Decide remaining stage integration or retirement separately. | Do not describe reasoning as the default public path. |
| TD-015 | Configuration portion resolved in Sprint 7: URL, model, and positive timeout come from `Settings` and are injected into `OllamaClient`. Public reasoning selection remains deliberately disabled. | Deployment values can vary without Core changes; activation policy is still undefined. | Partially resolved | Define policy before enabling reasoning publicly. | Do not silently activate Ollama or add fallback providers. |
| TD-016 | The local execution environment may provide invalid pre-existing settings such as `DEBUG=release`, while `.env.example` documents the valid boolean `DEBUG=true`. | Full application imports fail until deployment values match their declared types. | Low | Environment/deployment hygiene. | Do not weaken unrelated Settings validation to mask invalid environment values. |
| TD-017 | Sprint 8 resolves deterministic reasoning selection through `REASONING_ENABLED`, but the flag does not verify provider availability and no fallback exists by design. | Explicit activation can surface provider/network failure directly. | Accepted v1 limitation | Define availability and operational policy in later approved scope. | Do not add silent fallback, health checks, or retries opportunistically. |
| TD-012 | Resolved for structured success/failure in Sprint 10: `ResponseStage` returns `CognitiveOutcome`; the API safely maps stable codes to HTTP. Rich evidence-oriented content remains future scope, not a defect in this contract. | Controlled failures are no longer successful text/HTTP 200 responses. | Resolved for v1 | Sprint 10 | Preserve the Core/HTTP boundary and do not expose internal errors. |
| TD-013 | pytest reports a cache-path warning (`WinError 183`) while all 9 configured tests pass. | Test result is valid but local cache maintenance is degraded. | Low | Local tooling maintenance. | Do not change application architecture to address a cache warning. |
| TD-014 | Product identity is Luxiom, while README, package name, settings, architectural history, and module paths contain JARVIS-OS/JARVIS terminology. | Onboarding and release identity are ambiguous. | Medium | Planned migration with compatibility assessment. | Do not rebrand opportunistically. |

# Technical Debt

## Sprint 27 released classification

No new uncontrolled technical debt is identified in the implemented trusted
request-context foundation. The configured resolver and routing service are
deterministic, transport-neutral, explicitly composed, independently tested,
and guarded by architecture tests.

Public authentication, sessions/accounts, durable workspace membership,
transport/header integration, public HTTP protection, persistence, and
runtime grant/revoke behavior remain inherited or deliberately deferred future
work. They are not capabilities claimed by Sprint 27 and are not defects
introduced by its internal configured boundary. `ActorIdentity` and
`WorkspaceIdentity` remain typed values rather than authentication or access
proof.

## Sprint 26 merged-release classification

No new technical debt is identified. The implementation extends the existing
typed path, centralizes the 50/51 bounds, keeps public truncation in the
capability, and explicitly aligns Python ordinal ordering with SQLite BINARY
ordering. Pagination, a secondary index, fuzzy/semantic search, filterless
listing, public API exposure, generic criteria, configurable limits, ranking,
and model-assisted interpretation are deliberate narrow-scope deferrals.

## Sprint 25 classification

New technical debt introduced: none identified. Sprint 25 extends the existing
immutable interpreter contract and reuses all local knowledge components.
Richer grammar, multilingual or conversational interpretation, fuzzy matching,
model-assisted extraction, public HTTP exposure, authentication/RBAC, semantic
retrieval, synchronization, encryption, retention and external access remain
deliberate deferrals rather than implementation debt.

## Sprint 24 classification

New technical debt introduced: none identified. The immutable interpreter and
router are injected, deterministic, infrastructure-independent, and composed
once. Inherited debt remains separate.

Deliberately deferred: richer grammar, multilingual interpretation,
conversational context, ambiguity resolution, fuzzy matching, model-assisted
intent extraction, public HTTP integration, authentication/RBAC, semantic
retrieval, durable knowledge prompt use, synchronization, encryption,
retention, and external access.

## Sprint 23 classification

Inherited debt remains: unauthenticated identity, provisional goal/domain
routing, legacy parallel modules, and incomplete lifecycle scaffolds.

Deliberately deferred scope includes public coordinator HTTP exposure,
natural-language intent extraction, authentication/RBAC, semantic retrieval,
knowledge prompt integration, synchronization, encryption, retention, and
external-access policy. These are not defects introduced by the coordinator.

New technical debt introduced by Sprint 23: none identified. The coordinator
is typed, explicitly authorized, independently testable, and composed once.

## Sprint 22 limitations

SQLite durability is local to one explicitly supplied database. Luxiom still
lacks authenticated identity, natural-language local routing, public
local-first HTTP, automatic resolve-or-reason orchestration, multi-device sync,
encryption at rest, deletion/retention policy, semantic retrieval, truth
validation, automatic ingestion, and durable-knowledge prompt integration.
This is a durable foundation, not a complete Knowledge Engine.

## Sprint 21 limitations

The Sprint 21 default structured-list repository is ephemeral; Sprint 22 adds
an explicitly injected durable alternative without changing that default.
Typed commands are built directly; natural language is not converted to local
intents. Actor identity is explicit but unauthenticated, permissions are a
small deterministic policy rather than RBAC, and workspace identity is not a
durable product workspace. Local-first covers one generic capability, not
general knowledge retrieval. There is no external-access policy engine,
mobile/smart-glasses interface, automatic ingestion or synchronization.
Existing memory/reasoning routes may still use models when explicitly invoked.
`LocalFirstResolver` is composed but not integrated into `CognitiveEngine`, the
public API, natural-language extraction, or an automatic resolve-or-reason
orchestrator. Its `not_handled` result requires a caller to choose the separate
historical cognitive route; it is not an automatic fallback.

Sprint 23 partially resolves explicit coordination through
`LocalFirstCognitiveCoordinator`. A caller must still invoke that coordinator
and explicitly authorize fallback. Public HTTP integration, natural-language
extraction, authentication, and automatic fallback remain deferred; this is
not full product integration.

Separate verifier clients may use identical or correlated models; readiness
does not demonstrate semantic quality or epistemic independence.

Model-assisted verification can falsely support or reject claims. Shared mode,
or independent mode without an explicit model override, may reuse the same
configured generation model and therefore provides no model diversity.

Sprint 18's prompt builder and claim provider each recompute the deterministic
bounded selection with the same selector instance and immutable snapshot. This
is not a second retrieval or repository access.

Claim references are structurally validated but not semantically verified;
claims may also be compound rather than atomic.

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

## Sprint 14 classification

- Technical debt: global legacy memory, unowned legacy data, and the
  historically imprecise `OLLAMA_BASE_URL` name.
- Deliberately deferred: advanced stored prompt-injection defenses,
  selection/ranking, durable memory, writes, migration, identity,
  retention/deletion, tokenizer support, and token limits.
- Governance maintenance: synchronize explicit AST lists whenever
  prompt-policy consumers change.

## Sprint 16 classification

- Technical debt: global legacy memory, legacy data without ownership, and the
  historically imprecise `OLLAMA_BASE_URL` name remain.
- Deliberately deferred: durable persistence, delete/update, deduplication,
  retention, migration, identity, HTTP scope/update, automatic extraction,
  memory selection, advanced prompt-injection defense, concurrency, and token
  limits.
- Governance maintenance: keep explicit AST lists synchronized as writer,
  service, operational runtime, and CLI surfaces evolve.

Sprint 16 partially resolves TD-005 through a separate explicit local update
operation. The canonical `CognitiveEngine` lifecycle still performs no
automatic Memory Update, by design.

## Sprint 17 classification

- Resolved for v1: strict grounded envelope parsing, bounded visible-reference
  validation, controlled protocol failure, and deterministic insufficient
  evidence handling.
- Deliberately deferred: semantic claim verification, fact checking, a second
  evaluator model, external retrieval, embeddings, advanced injection defense,
  tokenizer accounting, persistence, identity, retries, JSON repair, and
  free-text fallback.

## Sprint 28 post-release classification

The migration atomicity defect found during Block C review was corrected and
regression-tested before immutable release `sprint-28-complete`; it is not
outstanding debt. Inherited or deliberately
deferred areas include authenticated principals, durable permissions,
public-route integration, roles/invitations, transition history, and transport
authentication. This does not claim zero project-wide technical debt.
- Accepted limitation: valid record numbers do not prove that every generated
  claim is supported by those records.
- Governance maintenance: keep explicit grounding and operational AST lists
  synchronized as these surfaces evolve.
# Sprint 29 deliberate future work

The following are deliberate deferrals, not defects in the bounded Sprint 29
candidate: production credential verification and security design; durable
principal, credential/verifier, and principal-to-actor mapping storage; secure
secret management; session, device, and public-transport integration;
credential reset/recovery; and remote identity-provider integration if later
authorized. These concerns must not be folded into current membership tables.

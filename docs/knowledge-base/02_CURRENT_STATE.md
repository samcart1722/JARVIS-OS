# Current State

## Sprint 35 governed implementation state

Sprint 35 is current: baseline `ade9a28d45a34b01e1279bc406b7336234e173e2`,
implementation `fd6ecb3a07c9b640892df40561006d79f531c622`, PR #52, ordinary
two-parent merge `c2dbab846cc7116568f59786233b64c0f01ab038`, tree
`c65d2bed9158e2630c0912e398bc09eb30a5405e`, and immutable tag
`governed-sprint-35-complete` (object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`, peeling to the merge).

Successful authorized list ADD/READ results now cross the application boundary
through the closed immutable union `LocalListAddProjection |
LocalListReadProjection`. The gateway correlates the already interpreted typed
intent with `LocalResolutionResult` without reparsing request text. ADD exposes
`list_id`, `added`, `already_present`, and final `items`; READ exposes `list_id`
and ordered `items`, including empty results. Dedicated HTTP models serialize
the exact variants. When projection is absent, only that member is omitted;
historical explicit nulls remain and no global `exclude_none` policy exists.

The minimal UI renders ADD and READ fields safely with DOM/text operations,
uses exact em dash `—` for applicable empty arrays, clears stale projection state
synchronously before fetch and early CSRF return, and hides ADD-only rows for
READ. Canonical `List updated locally.` and `List read locally.` responses stay
unchanged. Authentication, mapping, workspace selection, membership,
`PermissionPolicy`, routing, SQLite/schema v4, loopback transport, local-first
behavior, and fallback defaults remain unchanged. No generic/knowledge
projection, Cognitive Core contract, browser persistence, provider/network,
Hermes, or Spatial implementation was added.

Final validation passed 1,535 repository tests, Ruff, `compileall`, and release
diff check; post-merge operational proof and manual browser acceptance passed.
The governed backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35`.

## Historical Sprint 34 governed implementation state

At its release checkpoint Sprint 34 was current: baseline
`227c03e4f5b824710aebea38c5c6dd705e4ec44a`,
implementation `3f48e7fe9cf311df8b3bd2462a1987f8e732303d`, PR #50, merge
`adbd17d564962c6d22617b5857aaaec7da051b08`, tree
`a82e5c4c56b9fdb8660ef0fd878ea89364514b54`, tag
`governed-sprint-34-complete`, object `ae5557c26a719b4cdedef202a191fe92e15a57d3`.
The development-only separate Windows/Uvicorn app is fixed at
`127.0.0.1:8765`; `/local/ui` uses exact Host/Origin, strict JSON, runtime CSRF,
CSP, no-store, local assets, no CORS, and governed `POST /local/command`. UI
owns no downstream authority. Proof is separately entered and never transferred
or persisted. Storage is `Path.home()/.luxiom/development/local-interactive/
luxiom-local.sqlite3`, schema v4, no migration. External two-process proof
passed `alpha`, `beta`, 403 `access_denied`, and 403
`local_permission_denied`. Validation passed demo, architecture 144, repository
1433, Ruff, and diff-check; no GitHub checks. Backup:
`LUXIOM_20260827_165704_SPRINT34`.

## Historical Sprint 33 governed implementation state

At the Sprint 33 release checkpoint, Sprint 33 - Durable Action Permission
Revocation Foundation v1 was the latest governed implementation release.
Implementation commit
`9f4b86beddaa1e2550e054a55e6c743c87f2723c` merged through PR #48 at ordinary
two-parent release commit `9af9984691b034710243e1da487767108915ce3a`,
release tree `3a1317dc1a1c295ae5e2b77947a149cf138134ba`.

The historical `PermissionGrantRepository` remains exactly `is_granted` and
`create`. Sprint 33 adds the separate `PermissionGrantRevocationRepository`
with exactly `revoke`. `SQLitePermissionGrantRepository` structurally
implements both ports. `PermissionPolicy` remains exactly `is_allowed`, and
`RepositoryPermissionPolicy` remains an authorization-read-only consumer.

Revocation validates exact `ActorIdentity`, exact `WorkspaceIdentity`, and an
exact nonblank string action without normalization. Matching remains
case-sensitive and whitespace-bearing actions remain exact. One physical
SQLite `DELETE` removes only the exact actor/workspace/action row. Present and
absent revocations both commit and return `None`; prior existence and row count
are not disclosed. Unrelated grants survive and later re-grant through
`create` remains valid. Declared persistence failures use the stable
`PermissionGrantRepositoryError` boundary.

Schema version remains 4 with no migration or permission-schema change. Sprint
33 adds no audit history, soft delete, expiry, revoker identity, RBAC, public
permission administration, Container management composition, or public revoke
endpoint. Authentication, mapping, workspace selection, membership, routing,
and action authorization remain separate.

The deterministic operations proof passed in two separate Python interpreter
processes against the same external SQLite database: `revoke` proved create,
allow, revoke, and deny; `verify` used fresh storage, schema verification,
repository, and policy to prove the grant remained absent and authorization
remained denied.

Post-merge validation passed 134 architecture and 1,293 repository tests,
Ruff, `compileall`, and `git diff --check`. GitHub reported no CI/status checks.
The immutable tag is `governed-sprint-33-complete`, annotated object
`4d0774ee5172da9eff0ee246011775980aac367f`, peeling to the release commit.
The verified backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260826_122727`. Feature-branch cleanup
completed locally and remotely. This documentation synchronization is later
post-release reporting and does not move the immutable Sprint 33 checkpoint or
authorize/freeze Sprint 34.

## Sprint 31 governed implementation state

Sprint 31 - Durable Action Permission Foundation v1 is a historical governed implementation release. PR #40 merged at
`9cad78ed22f0a6aef26eda0623d0f544cf65e5be`, and the immutable governed tag is
`governed-sprint-31-complete`. The implementation, post-merge validation, tag
verification, and authoritative backup `LUXIOM_20260821_095503` are complete.

Sprint 31 adds durable exact actor/workspace/action permission grants behind the
existing `PermissionPolicy` boundary. It does not add roles/RBAC, inheritance,
wildcards, public permission administration, production authentication, or
sessions. Independent review was unavailable and no independent review is
claimed. Release-truth synchronization commit
`d79552f9ab19d7b2da9f2a60be4ef48b8b9608cd` merged through PR #41 at canonical
merge `7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`. Canonical validation passed 117
architecture and 1,119 repository tests, Ruff, and `git diff --check`. The
merged implementation and release-truth branches were deleted locally and
remotely. The full suite's initial Windows TEMP permission failure was
environmental; its controlled-basetemp rerun passed all 1,119 tests. The RT2B
documentation diff and PR #41 received independent post-edit and pre-merge
approval respectively; neither is an independent implementation review. This
closure-truth work merged through PR #42 at ordinary two-parent merge
`fa90defc44ad756a33f11e470105db57a440e201` after final independent pre-merge
approval. Final canonical validation passed 117 architecture and 1,119
repository tests, Ruff, and `git diff --check`. All governed Sprint 31
implementation, release-truth, and closure working branches were merged and
cleaned locally and remotely before this post-closure documentation record.
Final governance verification confirmed the closure conditions, so Sprint 31
is formally governance-closed at that canonical checkpoint. This record reports
the already-established state and does not create it.

## Sprint 29 released implementation state

Local Principal Authentication Foundation v1 is released through PR #34 at
`9590beca0ddfce544f774ffc1327d01f8044a420`, tag `sprint-29-complete` (object
`c3a204555cc512ae9404039aeb8be8d6aa421550`). It provides local authenticated
routing while keeping Sprint 28 membership, Sprint 27 non-authenticated trusted
context, and `PermissionPolicy` action authorization separate. Configured
authentication is process-local/nonpersistent, not production authentication.
Authentication is neither membership nor action authorization;
`PrincipalIdentity` is distinct from `ActorIdentity`; trusted binding is
neither authentication nor durable membership; workspace selection is not
membership admission; membership is workspace admission only; and
`PermissionPolicy` remains action authorization. Public authentication APIs,
JWT/OAuth, sessions, production password/PIN/device/biometric authentication,
durable authentication or credential state, and production account lifecycle
remain deferred.
Validation passed 1,035 repository tests and 8/8 authenticated plus 7/7 trusted
demos. The authoritative backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_141402`.

## Sprint 28 released implementation state

Sprint 28 Durable Actor–Workspace Membership Foundation v1 was independently
approved, merged through PR #32 using a normal merge commit, and post-merge
validated. Feature commit `95341198145f84d80c7cf37bf73b707cfe574a21`
is the second parent of release commit
`be22ffddda6d6961497c338caadf4c85e0fcb3ed`. Annotated tag
`sprint-28-complete` has object
`986ae13ca8fefcbd6197db8a723e25ae4e3dc62a` and peels to that release commit.
The independently recoverable backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260817_190455`.

Validation passed 28 SQLite, 41 membership, 29 Container, 130 trusted-context,
156 focused Sprint 28, 78 architecture, and 915 repository tests; Ruff and
diff checks were clean. Both demos passed with
model/provider/readiness/network calls of `0 / 0 / 0 / 0`. Sprint 29 Local
Principal Authentication Foundation v1 is released and implementation-complete
through PR #34 at `9590beca0ddfce544f774ffc1327d01f8044a420`. Its immutable
tag `sprint-29-complete`, object
`c3a204555cc512ae9404039aeb8be8d6aa421550`, peels to that released commit; its
verified authoritative backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_141402`.

## Sprint 27 fully released state

Sprint 27 Trusted Request Context Foundation v1 is merged into canonical
`master` through PR #29. Its feature commit is
`feb5405d9c0dae123c366dc4ce405fb9e9f2a30a`, its functional merge is
`758e63278f0b342302dd1ed0d41f8514d1d9f1c3`, and post-merge validation passed
836 tests. Release-truth commit `0e220a789d683d49f4ac360cf70c65511ad96446`
merged through governance PR #30, and the annotated `sprint-27-complete` tag
points to release commit `1501183b4c40faaba278f8d61f875d65954223a7`.
The `app/cognition/trusted_context` package provides immutable
request/context/results, the
`TrustedRequestContextResolver` port, a deterministic
`ConfiguredTrustedRequestContextResolver`, and
`TrustedLocalCommandRoutingService`.

`Container` composes one resolver and one trusted routing service around the
existing `LocalCommandTextRouter`. Architecture tests enforce the supported
path and dependency direction. The internal deterministic demo exercises seven
trust, workspace, authorization, and payload scenarios with zero remote
boundaries. Public HTTP, legacy `/knowledge`, and `CognitiveEngine` remain
disconnected from this boundary. This is internal configured trust resolution,
not authentication or durable membership. Final validation passed 117 focused,
70 architecture, and 836 repository tests, Ruff, and the 7/7 demo. The verified
release backup is `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260807_160935`.

## Sprint 26 released canonical state

Canonical `master` implements deterministic local discovery through
`knowledge find :: {"key":"..."}` with an optional exact
`kind`. Discovery is workspace-scoped, authorized by
`knowledge.records.read`, ordered by case-sensitive record ID, capped at 50
visible records with one lookahead row, and returns empty success for zero
matches. Public HTTP, cognitive contracts, Settings, dependencies, RBAC, and
SQLite schema version 1 remain unchanged. The functional implementation merged
at `54e04261933ab85dbe4b237e6f81037d508b4a1c`; the final canonical Sprint 26
release commit is `ae13c3ed9720ee9564384366f2110670eb88fd85`. Sprint 26 is
fully released at the annotated tag `sprint-26-complete` and is the latest
completed tagged release.

## Sprint 25 executable state

Sprint 25 is completed through merged PR #24 at
`1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`
(annotated tag object `6e0de87b426e4a7d4c3103bdffc77f2b171aa30f`).
The existing interpreter maps strict JSON knowledge commands
to existing typed knowledge intents. Workspace comes from the routing request,
not text; caller-supplied provenance is preserved. Malformed recognized
knowledge commands are terminal. Public HTTP and `CognitiveEngine` are unchanged.

This boundary is not broad natural-language understanding or a model
classifier. A cognitive route also does not imply model execution when the
existing settings choose the deterministic cognitive capability.

## Sprint 23 released foundation

Sprint 23 is released at merge `be59175c201df1f2458551d99e2f5dcc3e9d2aac`,
tag `sprint-23-complete`. One explicit coordinator calls `LocalFirstResolver`
first. A handled
local result is terminal. Only `not_handled` plus explicit authorization and a
valid non-blank cognitive input invokes the existing cognitive path.

The coordinator accepts already-typed intents and is not called by public HTTP.
No natural-language parser or automatic bridge was added to `CognitiveEngine`.

The repository now contains an ephemeral, workspace-scoped structured-list
capability with explicit actor and deny-by-default permission policy. Typed add
and read intents resolve deterministically with model/external call counts of
zero. `LocalFirstResolver` returns `not_handled` for unsupported typed intents;
the pre-existing reasoning path remains separately available, but no automatic
bridge chooses between them.
This supersedes older checkpoint counts below as current operational truth;
those figures remain historical evidence.

> Sprint 20 optionally separates generator and verifier client configuration;
> shared-client Sprint 19 behavior remains the default.

> Sprint 19 optionally applies one model-assisted, all-or-nothing claim support
> gate. It does not prove truth or factual accuracy.

> Sprint 18 adds opt-in structural references per claim while preserving the
> historical and Sprint 17 paths. It does not verify semantic support.

Historical checkpoint snapshot through Sprint 28: **2026-08-17**
(America/Tegucigalpa).

## Historical repository checkpoint through Sprint 28

- Canonical branch: `master`
- Sprint 28 tagged implementation release commit:
  `be22ffddda6d6961497c338caadf4c85e0fcb3ed`
- Latest immutable implementation release tag at this historical checkpoint:
  `sprint-28-complete`
- Sprint 28 annotated tag object:
  `986ae13ca8fefcbd6197db8a723e25ae4e3dc62a`
- Sprint 28 verified release backup:
  `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260817_190455`
- Sprint 27 tagged release commit:
  `1501183b4c40faaba278f8d61f875d65954223a7`
- Sprint 27 annotated tag object:
  `35a198af85299e9e09d086e63f66020ccdc522d3`
- Sprint 26 annotated tag object:
  `fc8b8a403e920f547a72783a296bd7ef406e7033`
- Sprint 26 peeled release commit:
  `ae13c3ed9720ee9564384366f2110670eb88fd85`
- Sprint 25.1 state: completed, merged, and tagged.
- Sprint 26 state: fully released from `master` at tag `sprint-26-complete`.
- Sprint 27 state: fully released and tagged at `1501183b`, with verified
  release backup `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260807_160935`.

## Confirmed stack

- Python project requiring Python `>=3.12`; verification ran on Python 3.14.6.
- FastAPI, Pydantic, pydantic-settings, and Loguru are runtime dependencies.
- pytest, pytest-cov, Ruff, and Pyright are declared development dependencies.
- setuptools/wheel build backend.
- The active repository name/package metadata still says `JARVIS-OS` /
  `jarvis-os`; this conflicts with the verified Luxiom product identity.

Source: `pyproject.toml`, `app/main.py`, and `app/core/config.py`.

## Main structure

- `app/cognition/`: current Cognitive Core models, contracts, pipeline pieces,
  memory implementation, and integrated engine.
- `app/core/container.py`: composition root for memory and the cognitive engine.
- `app/brain/`, `app/memory/`, `app/reasoning/`: older application paths still
  present; `app/brain` bridges the HTTP route to the new engine.
- `app/api/`: FastAPI routes.
- `tests/`: configured pytest suite for the current sprints.
- `app/tests/`: legacy tests present but excluded by configured `testpaths`.
- `docs/`: foundation, architecture, RFC, implementation, and recovery material.

## Historical sprint status through Sprint 28

| Sprint | State | Confirmed result |
|---|---|---|
| 0 | Completed/tagged | Cognitive engine entry point and legacy memory compatibility restored. |
| 1 | Completed/tagged | Minimal cognitive pipeline and replaceable reasoning-provider contract added. |
| 2 | Completed/tagged | Core goal, context, domain, specialist, plan, executor, and capability contracts added; Product North Star and Cognitive Lifecycle added. |
| 3 | Completed/tagged | Executable classification → specialist → plan → execution → response flow wired in `Container` and tested. |
| 4 | Completed/tagged | Public cognitive input calls the Container-composed `CognitiveEngine`; behavioral API tests verify the boundary. |
| 5 | Completed/tagged | Capability Runtime v1 resolves and executes a registered deterministic capability. |
| 6 | Completed/tagged | Provider-backed `ReasoningCapability` is executable on demand without changing default policy. |
| 7 | Completed/tagged | Ollama URL, model, and timeout use validated settings and explicit composition. |
| 8 | Completed/tagged | Deterministic policy selects normalized input or reasoning from explicit enablement. |
| 9 | Completed/tagged | Active Core documentation and architecture enforcement protect executable boundaries. |
| 10 | Completed/tagged | Structured outcomes and safe HTTP failure mapping are integrated. |
| 11 | Completed/tagged | Explicit Ollama readiness and controlled opt-in reasoning demo were added outside Core/API. |
| 12 | Completed/tagged | Scoped in-memory repository contracts enforce ownership and isolation. |
| 13 | Completed/tagged | Optional scoped retrieval enriches context only when enabled and explicitly scoped. |
| 14 | Completed/tagged | Bounded memory-aware prompt policy preserves exact default behavior. |
| 15 | Completed/tagged | Controlled baseline/scoped-memory comparison demo proves isolated behavior. |
| 16 | Completed/tagged | Explicit opt-in scoped writes support a controlled ephemeral demo. |
| 17 | Completed/tagged | Evidence-bounded reasoning validates a strict envelope and bounded references. |
| 18 | Completed/tagged | Claim-level evidence attribution adds structurally auditable references. |
| 19 | Completed/tagged | Model-assisted claim support verification remains optional and controlled. |
| 20 | Completed/tagged | Independent verifier-client composition remains opt-in. |
| 21 | Completed/tagged | Released at `8c0330b`, tag `sprint-21-complete`; typed local lists add explicit identity, workspace, permissions and zero-call deterministic execution. |
| 22 | Completed/tagged | Released at `9dcb36b`, tag `sprint-22-complete`; explicit SQLite adapters persist typed lists and minimal provenance-bearing knowledge. |
| 23 | Completed/tagged | Released at merge `be59175c201df1f2458551d99e2f5dcc3e9d2aac`, tag `sprint-23-complete`; explicit typed local-first coordination remains outside public HTTP and `CognitiveEngine`. |
| 24 | Completed/tagged | Released at merge `fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`; bounded list-command interpretation remains outside public HTTP. |
| 25 | Completed/tagged | Released through PR #24 at merge `1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`; strict JSON knowledge commands reuse the existing local-first interpretation and routing path. |
| 26 | Completed/tagged | Deterministic exact-key local knowledge discovery is released at `ae13c3ed`, tag `sprint-26-complete`. |
| 27 | Completed/tagged | Internal configured trusted-context resolution, supported trusted routing, Container composition, architecture enforcement, and deterministic demo released at `1501183b`, tag `sprint-27-complete`; final validation passed 117 focused, 70 architecture, and 836 repository tests. |
| 28 | Completed/tagged/backed up | Durable actor/workspace membership released through PR #32 at `be22ffdd`, tag `sprint-28-complete`; independently validated and recovered from `LUXIOM_20260817_190455`. |

## Executable components and status

| Component | Classification | Evidence |
|---|---|---|
| `CognitiveEngine.process` | Integrated | Constructs `Goal`/`CognitiveContext`, classifies, routes, plans, executes, and formats. |
| `Container` | Integrated, partially scaffolded | Builds memory and cognitive engine; several `_build_*` methods are `pass`. |
| `DefaultGoalClassifier` | Provisional | Always returns `Domain.UNKNOWN`. |
| `SpecialistRouter` | Provisional | Maps every domain to one `DefaultSpecialist`. |
| `DefaultSpecialist` | Provisional | Creates one step requesting the logical `normalized_input` capability. |
| `CapabilityRegistry` | Integrated v1 | Maps stable logical identifiers to injected implementations and detects duplicate or missing identifiers. |
| `CapabilityExecutor` | Integrated v1 | Executes registered capabilities sequentially with context and fail-fast behavior. |
| `NormalizedInputCapability` | Integrated bootstrap capability | Deterministically returns normalized context input; performs no reasoning and uses no external service. |
| `ReasoningCapability` | Integrated, opt-in | Uses `ReasoningStage` and the `ReasoningProvider` port; registered but not selected by `DefaultSpecialist`. |
| `DeterministicReasoningSelectionPolicy` | Integrated | Selects one official capability identifier from immutable boolean enablement; it does not inspect prompts or providers. |
| `DefaultSpecialist` | Policy-driven | Receives `CognitiveContext`, delegates selection once, and constructs the same one-step plan shape. |
| `OllamaProvider` | Composed, not publicly activated | Receives a configured `OllamaClient`; construction performs no network call. |
| Ollama settings | Integrated | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and positive `OLLAMA_TIMEOUT_SECONDS` support environment overrides. |
| Cognitive Core governance docs | Complete for active v1 runtime | Components, contracts, Core/infrastructure boundaries, legacy exclusions, and known debt are documented. |
| Architecture tests | Integrated | Protect explicit active-file import, composition, documentation, and local-resolution boundaries using the standard library. |
| `CognitiveOutcome` / `CognitiveError` | Integrated | Enforce valid success/failure states and stable provider-independent errors. |
| `ResponseStage` | Integrated structured boundary | Returns real output as success or a structured controlled failure; it knows no HTTP. |
| Cognitive memory pipeline | Implemented and composed | Built in `Container`, exposed through a legacy adapter, but absent from the integrated request cycle. |
| Concrete capabilities | Integrated in separate paths | `NormalizedInputCapability` and `ReasoningCapability` remain in the historical engine. Separate `StructuredListCapability` and `StructuredKnowledgeCapability` serve typed local intents outside `CognitiveEngine` and public HTTP. |
| `LocalFirstCognitiveCoordinator` | Composed, explicit application boundary | Preserves handled local results; only authorized valid `not_handled` requests call the existing cognitive processor. Public HTTP does not use it. |
| `DeterministicLocalCommandInterpreter` | Implemented, bounded application interpretation | Maps only the narrow list-command grammar to existing typed intents; it is not general natural-language understanding. |
| `LocalCommandTextRouter` | Composed, explicit application boundary | Invokes the existing Sprint 23 coordinator for bounded commands. Public HTTP and `CognitiveEngine` do not use this service. |
| `ConfiguredTrustedRequestContextResolver` | Implemented, process-local configuration boundary | Resolves explicit configured actor/workspace context without persistence, network, or default workspace selection. |
| `TrustedLocalCommandRoutingService` | Composed, supported internal application boundary | Resolves trust before delegating to the existing text router; trust failures short-circuit. Public HTTP does not use it. |
| `InputStage` / `ContextStage` / `ReasoningStage` | Implemented separately | Not called by the Sprint 3 `CognitiveEngine.process` path. |

## Real request flow

The FastAPI `/brain/think` route obtains the already-composed engine from the
module-level `Container` instance and calls
`container.cognitive_engine.process` directly. The engine runs:

`user_input → Goal + CognitiveContext → Domain → Specialist → Plan →
CapabilityRegistry → NormalizedInputCapability → CapabilityResult →
ExecutionResult → ResponseStage → str`

See [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md) for exact boundaries.

## Tests

Command: `.\.venv\Scripts\python.exe -m pytest`

Sprint 25 release validation: **680 passed** with `DEBUG=true`, including **85
focused tests**; Ruff and `git diff --check` passed using controlled external
Sprint 25 pytest temporary directories.

Historical Sprint 24 feature-tree result: **625 passed** with `DEBUG=true`;
Ruff and `git diff --check` passed using a controlled external pytest temporary
directory. Sprint 24 was subsequently released at
`fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`.

Historical Sprint 23 feature-tree result: **591 passed** with `DEBUG=true`;
Ruff and `git diff --check` passed using controlled external pytest temporary
files. Sprint 23 was subsequently released at
`be59175c201df1f2458551d99e2f5dcc3e9d2aac`, tag `sprint-23-complete`.

Sprint 22 released baseline result: **570 passed** with `DEBUG=true`; Ruff and
`git diff --check` passed.

Sprint 21 baseline result: **534 passed** with `DEBUG=true`; Ruff and
`git diff --check` passed. The older counts below are historical checkpoints.

Sprint 4 baseline: **9 passed, 1 warning in 0.14s**.

Sprint 5 baseline: **12 passed, 1 warning in 0.96s**.

Sprint 6 baseline: **24 passed, 1 warning in 0.86s**.

Sprint 7 baseline: **34 passed, 1 warning in 1.05s**.

Sprint 8 baseline: **45 passed, 1 warning in 1.05s**; Ruff passed and
`git diff --check` was clean.

Sprint 9 baseline: **63 passed, 1 warning in 0.87s**; Ruff and
`git diff --check` passed.

Sprint 9 final result: **70 passed, 1 warning in 1.10s** with `DEBUG=true`.
The warning remains the pre-existing pytest cache-path warning. Seven new
tests protect confirmed boundaries and minimum governance-document coverage.
Tests under `app/tests/` remain excluded.

Sprint 10 baseline: **70 passed, 1 warning in 1.69s**; Ruff and
`git diff --check` passed. Final Sprint 10 results are recorded in its summary.

Sprint 11 baseline: **86 passed, 1 warning in 1.84s**; Ruff and
`git diff --check` passed. Readiness uses one on-demand `GET /api/tags`;
construction and the default API path remain network-free.

Sprint 12 baseline: **111 passed, 1 warning in 1.36s**. The scoped foundation
is deliberately not composed into the active runtime.

Sprint 13 baseline: **130 passed, 1 warning in 1.30s**. Container now composes
an empty scoped repository; public requests still supply no scope and perform
no retrieval.

Sprint 14 baseline: **154 passed, 1 warning in 1.26s**. Prompt memory defaults
off and remains unreachable from the unscoped public route.

Sprint 15 baseline: **192 passed, 1 warning in 2.33s**. The functional demo
adds an explicit local comparison; the unscoped public route remains
unchanged.

Sprint 16 baseline: **221 passed, 1 warning in 1.47s**. Explicit update remains
disabled by default and absent from the public route.

Sprint 17 adds opt-in evidence-bounded response parsing and auditable selected
record numbers. It defaults off; absent or empty memory preserves the exact
historical path. The protocol validates structure and references, not truth or
semantic support, and the public route still supplies no scope.

## Integration limit and undecided items

The local resolver is not called by `CognitiveEngine.process`, the public API,
natural-language intent extraction, or an automatic resolve-or-reason
orchestrator. Default repositories are ephemeral; explicit operations
composition can inject SQLite durability. Production/public/durable identity
authentication, integration policy, encryption, synchronization, retention,
semantic retrieval, truth validation, and external-access governance remain
deferred.

`app/brain/Brain` and `app/brain/Orchestrator` remain present but have no
consumer in the public cognitive route. Other historical modules under
`app/reasoning`, `app/context`, and `app/memory` remain outside this sprint.

## Sprint 28 closure lineage and subsequent Sprint 29 governance

Implementation, review, merge, post-merge validation, immutable tagging, tag
verification, and recoverable backup verification are complete.
Sprint 29 release-truth metadata governance completed through metadata commit `854e767d86443db860eb8e23b75a736d1266b394`, branch push, PR #35, and ordinary merge `9a441706280b22d6471b0ecff5b47ff78617a467` into `master`. Final Sprint 29 release closure and branch cleanup subsequently completed before the governed Sprint 30 base.
# Sprint 29 released feature

The released implementation provides a local principal-authentication foundation
and authenticated internal routing. Its configured deterministic authenticator
is non-production, process-local, and nonpersistent. Principal-to-actor mapping
is explicit; workspace selection, membership admission, and permission
authorization remain separate stages. The trusted route remains separate and
non-authenticated.

Public transport authentication, production credential technology, and durable credential or principal-account storage remain unintegrated. Sprint 29 is released, tagged, authoritatively backed up, and implementation-complete. Sprint 30 subsequently adds durable principal-to-actor mapping only.

## Sprint 30 released implementation state

**Sprint 30 — Durable Principal–Actor Mapping Foundation v1** is released.

The governed feature commit is `4516dfb13d1fc27eecdb3ae0090fb1f786130c4c`. It merged through PR #37 using
ordinary merge commit `6181f549c12195c69708ee2cfa53399a46fa4b29` with release tree `ab1d67907fddcce178559514f4efef533144e067`.

The immutable governed annotated release tag is `governed-sprint-30-complete`. Its tag object is
`cd410e5e0ddad708cd3b1a8b91b0fe4dc38e5f35` and it peels to `6181f549c12195c69708ee2cfa53399a46fa4b29`.

Sprint 30 adds durable persistence only for the exact
`PrincipalIdentity -> ActorIdentity` association while preserving the
separation between authentication, principal mapping, workspace selection,
membership admission, and downstream action authorization.

The durable mapping contract remains:

- one principal maps to at most one actor;
- multiple principals may map to the same actor;
- principal matching is exact and case-sensitive;
- missing mappings fail closed;
- repository/storage failures fail closed through the distinct
  `principal_mapping_resolution_failed` path;
- mapping creation does not overwrite, update, delete, or upsert an existing
  principal mapping;
- mapping persistence stores no credential, proof, verifier, secret, token,
  workspace, role, permission, membership state, or session;
- default `Container` composition remains no-I/O;
- SQLite durability requires explicit repository injection;
- public HTTP, `CognitiveEngine`, trusted routing, membership semantics, and
  `PermissionPolicy` remain unchanged.

SQLite local storage is schema v3 and includes
`principal_actor_mappings(principal_id TEXT NOT NULL COLLATE BINARY PRIMARY KEY,
actor_id TEXT NOT NULL)` with no unique actor constraint.

Post-merge validation on canonical `master` passed 1,059 repository tests,
Ruff, the Sprint 27 trusted-context demo, Sprint 29 local-principal
authentication demo, Sprint 28 durable-membership seed/verify proof, Sprint 30
durable principal/actor seed/verify proof, and direct SQLite-v3 contract
verification. Model/provider/readiness/network calls remained zero in the
required deterministic proofs.

The authoritative recoverable backup is:

`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_SPRINT30_20260819_173314`

Verified backup hashes:

- Git bundle SHA-256:
  `d70c758f760facf878e178c6adbd76a33246fa745c5d014512e9c320d8563514`
- raw-Git-blob source ZIP SHA-256:
  `1ab03cfa263822626e6c39e1385353cecdbb8a2e620ff2b70bf2c79949f07a22`
- source-blob manifest SHA-256:
  `3acb73b2c57fb9aabfae3dc9cfa1115040acdbf3b286776067a907c354f93a5a`
- backup manifest SHA-256:
  `52667d244182f0448270d76a145837baee8989cdbfc1b7ec605801aad68033a9`

Bundle recovery reproduced the exact released master/tree, governed tag object
and peel, and historical legacy tag. The source ZIP reproduced all 526 tracked
Git blobs byte-for-byte with matching per-file SHA-256 values.

The unrelated historical annotated tag `sprint-30` remains preserved and is
explicitly excluded from the governed Sprint 30 lifecycle. Its tag object
remains `d5794405f4a0c70dc750e7e4438ca7c10a198b04` and it peels to `a37dc884bd7b9962a5842037b52f2bf202f16b34`. It was not moved,
deleted, or reused.

The implementation release, immutable tag, authoritative backup, release-truth metadata integration, and mandatory final post-merge validation are complete. Metadata commit `a8bce2df7aa6903f29d7b88b6a976e504ba9268a` merged through PR #38 at ordinary merge `89d303407d0da4b2d2d12509fc8b5aef6d7fcb46`. Final validation on canonical `master` passed 1,059 repository tests, Ruff, and the governed Sprint 27, 28, 29, and 30 operational regressions. The bounded closure-truth correction subsequently completed before the governed Sprint 31 base.

Manual same-assistant governance reviews performed during this release cycle
are not represented as independent review.

## Sprint 31 released feature

Sprint 31 - Durable Action Permission Foundation v1 was implemented from frozen
base `a2ba79dc5deb70e6929cf4164ea8a0636ffc0dc9` and merged through PR #40 at
`9cad78ed22f0a6aef26eda0623d0f544cf65e5be`.

The governed release adds:

- PermissionGrantRepository;
- PermissionGrantRepositoryError;
- PermissionGrantConflict;
- RepositoryPermissionPolicy;
- SQLite schema v4 with action_permission_grants;
- additive rollback-safe v3 -> v4 migration;
- SQLitePermissionGrantRepository;
- explicit Container repository injection;
- architecture enforcement;
- deterministic seed/verify durable authorization proof.

The exact authorization dimensions are actor, workspace, and action.

A missing grant is denial. Declared repository/storage failure is denial.
Invalid repository boolean output is denial. Membership does not imply action
permission.

Post-correction validation passed 1,119 repository tests, including 117
architecture tests, plus global Ruff and git diff --check.

The operational proof passed with zero model, provider, readiness, network, and
cognitive-fallback calls.

Independent review was unavailable and no independent review is claimed.
Same-assistant technical and adversarial reviews must not be represented as
independent review. Commit, push, PR #40 merge, post-merge validation, immutable
tag `governed-sprint-31-complete`, tag verification, and authoritative backup
verification have completed. Release-truth PR #41 merged at
`7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`; mandatory canonical validation
passed 117 architecture and 1,119 repository tests, Ruff, and
`git diff --check`. The merged implementation and release-truth branches were
cleaned locally and remotely. PR #42 received final independent pre-merge
approval and merged through ordinary two-parent merge commit
`fa90defc44ad756a33f11e470105db57a440e201`. Final canonical validation passed,
the closure working branch was cleaned locally and remotely, and final
governance verification confirmed the closure conditions. Sprint 31 is formally
governance-closed at that canonical checkpoint; this post-closure documentation
record does not establish or condition that closure.

## Sprint 32 released feature

Sprint 32 - Authenticated Local Command Application Gateway v1 was implemented
from frozen base `7aa29bdc894fe646d9e76cb0466d2e26fd44bc88`.

Implementation commit:

`a56a11f1b92b08df5e310aea749d9cda07570b65`

PR #45 merged through ordinary two-parent merge commit:

`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`

with release tree:

`d9e31be190d8077886ce6f85642f9b89d1fd8529`

The governed release adds the framework-independent `app/local_command`
application boundary and the bounded local-use `POST /local/command`
development surface.

The supported dependency direction is:

`app/api` -> `app/local_command` ->
`AuthenticatedLocalCommandRoutingService` -> existing governed downstream
routing, authorization, and local-capability chain.

The application gateway preserves the existing separation of:

- authentication proof;
- principal authentication;
- principal-to-actor mapping;
- explicit workspace selection;
- membership admission;
- local command routing;
- `PermissionPolicy` action authorization;
- deterministic local capability resolution.

Cognitive fallback remains explicit and caller-authorized. It is never
automatic.

The application request and result contracts are closed and validated. Proof
material is treated as secret-aware opaque material and explicitly rejects
pickle serialization.

Unexpected application invariants are sanitized at the HTTP adapter rather than
exposing internal details.

Default `Container` composition remains rejecting, fail-closed, in-memory, and
construction-time no-I/O.

Sprint 32 does not add production authentication, durable credentials,
password/PIN/biometric/API-key technology, JWT/OAuth, sessions, device
lifecycle, RBAC, roles, public permission administration, public Internet
exposure, CORS, UI, runtime SQLite credential composition, or automatic
cognitive fallback.

Historical `/brain/think` and legacy `/knowledge` remain separate surfaces and
were not made authenticated by Sprint 32.

The first independent implementation review required correction for two HIGH
findings:

- proof material remained pickle-serializable;
- the initial external manifest hash semantics were incorrect.

Both findings were corrected and explicitly closed by the approving second
independent review. The staged-index attestation and final independent
pre-merge review also approved the release.

Post-merge validation passed:

- 129 architecture tests;
- 1,273 repository tests;
- Ruff;
- `compileall app tests`.

The immutable governed release tag is:

`governed-sprint-32-complete`

Annotated tag object:

`c1f4267177d316d303c8c4c0e7fd3728afdcad32`

The tag peels to immutable Sprint 32 implementation checkpoint:

`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`

The authoritative recoverable backup is:

`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260825_103049`

Sprint 32 is formally governance-closed.

A later post-closure canonical documentation synchronization merged through
PR #46 at:

`2a2639334ad1e75ccd9db1d7c640f1e07297a54e`

That documentation merge advances canonical `master` but does not move,
replace, retarget, or redefine the immutable Sprint 32 release checkpoint.

Sprint 32 is the immediately preceding governed implementation release. Its
completion did not itself authorize Sprint 33; Sprint 33 was separately frozen,
implemented, and released as recorded in the current section above.

# Local-First Knowledge and Model Policy

Version: 1.0
Status: Normative

## Sprint 30 durable principal-to-actor mapping release

The governed Sprint 30 release adds durable local persistence only for
the exact `PrincipalIdentity -> ActorIdentity` association. Authentication
still occurs first; workspace selection, membership admission, and downstream
`PermissionPolicy` remain later and separate boundaries.

The Core-facing `PrincipalActorMappingRepository` owns only `get` and `create`.
A missing mapping fails closed. Repository failure or invalid stored actor data
fails closed separately as `principal_mapping_resolution_failed`. Creation
never overwrites an existing principal, even when the requested actor is the
same. Multiple principals may map to one actor. Matching is exact and
case-sensitive.

SQLite schema v3 stores only `principal_id` and `actor_id`. It stores no
credential, proof, verifier, secret, token, workspace, role, permission,
membership status, session, or authentication state. Default `Container`
composition remains no-I/O; durable mapping requires explicit repository
injection.

The durable two-process demo proves persistence and successful local routing
with model/provider/readiness/network counts of zero. Public HTTP,
`CognitiveEngine`, the trusted route, membership semantics, and action
authorization remain unchanged.

The governed implementation merged through PR #37 at `6181f549c12195c69708ee2cfa53399a46fa4b29` and is
released at `governed-sprint-30-complete`. Its authoritative recoverable backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_SPRINT30_20260819_173314`.

## Sprint 27 trusted request-context boundary

For supported internal local text commands, deterministic trusted-context
resolution now precedes interpretation. A configured, process-local resolver
requires an explicit workspace and produces an immutable actor/workspace
context. It uses no model, provider, network, clock, randomness, persistence,
or schema.

Trust resolution does not authorize an action. After trust success, the
existing `PermissionPolicy` remains the downstream authorization boundary and
the existing cognitive fallback policy is unchanged. Trust failures terminate
before the low-level router. Sprint 27 does not connect this boundary to public
HTTP and does not establish authentication or durable membership.

## Sprint 26 canonical application

The Sprint 26 implementation merged into canonical `master` adds authorized,
workspace-scoped,
exact-key knowledge discovery with an optional exact kind. It returns at most
50 records in binary/ordinal record-ID order, uses one internal lookahead row,
and treats zero matches as local success. It performs no model, provider,
network, ranking, inference, or external access. The functional implementation
merged at `54e04261933ab85dbe4b237e6f81037d508b4a1c`; the final canonical
release commit is `ae13c3ed9720ee9564384366f2110670eb88fd85`. Sprint 26 is
fully released at the annotated tag `sprint-26-complete`. Sprint 27 subsequently
released trusted request context, Sprint 28 released durable membership, and
Sprint 31 is now the latest governed implementation release at
`governed-sprint-31-complete`.

## Policy

Luxiom resuelve en este orden: capability local determinista autorizada;
estado o conocimiento local autorizado; respuesta determinista si es
suficiente; modelo local cuando haga falta interpretación o síntesis; acceso
externo solamente bajo una futura política explícita; insuficiencia segura si
no existe ruta autorizada.

Offline-capable significa que una ruta soportada completa su trabajo sin
modelo, Internet ni servicio externo. Model-on-demand prohíbe invocar un modelo
para una solicitud estructurada ya resuelta, denegada o invalidada localmente.
El criterio zero-call debe demostrarse con observación de la frontera del
provider, no solo con metadatos.

Los intents tipados permiten ejecución determinista sin afirmar comprensión
general del lenguaje. Toda lectura o escritura exige actor, workspace y permiso
explícitos; las acciones desconocidas se deniegan. La autorización humana
continúa gobernando ejecución y acceso.

Memoria cognitiva, conocimiento durable, capturas, candidatos y conocimiento
validado son conceptos distintos. Una captura no es verdad; un candidato no es
conocimiento validado; memoria no pertenece al modelo. La intención de producto
incluye múltiples usuarios y workspaces sin privilegios implícitos.

Sprint 21 implementa solo una capability genérica de listas con repositorio en
memoria. No aporta persistencia durable, conversión de lenguaje natural,
ingestión automática, voz, aplicaciones móviles ni smart glasses. Tampoco existe
aún un motor de política para acceso externo. Si no hay ruta autorizada, el
sistema debe fallar de forma segura.

La implementación actual es una ruta tipada separada. `LocalFirstResolver`
devuelve `not_handled` para intents no soportados; `CognitiveEngine` permanece
disponible por separado. Sprint 21 no conecta automáticamente ambas rutas, no
integra el resolver en `CognitiveEngine.process` ni en la API pública, y no
incluye un orquestador automático resolve-or-reason.

El estándar ADR permanece Draft y pendiente de certificación; esta política no
presenta ningún ADR como aprobado.

## Sprint 25 deterministic knowledge commands

Sprint 25 extends the existing deterministic interpreter with strict JSON
knowledge commands. The routing request supplies workspace; command text cannot
supply or override it. Provenance remains caller-supplied and is preserved
exactly. Malformed recognized knowledge commands are terminal and never reach
cognition. This structured syntax is not general natural-language
understanding and changes no public HTTP, model, provider, or external access.

## Sprint 22 durable foundation

Sprint 22 añade adaptadores SQLite explícitos para listas y el registro mínimo
de conocimiento tipado, conservando al Core independiente de SQLite. La
identidad de conocimiento es `workspace_id + record_id`; la procedencia es
obligatoria y se conserva exactamente. Una escritura idéntica es idempotente,
una distinta produce conflicto controlado y una lectura ausente produce
`local_knowledge_not_found`.

Guardar no certifica verdad ni confianza. No hay sincronización, cifrado en
reposo, borrado/retención, búsqueda semántica, extracción automática ni
integración del conocimiento durable en prompts. Esta es una base durable, no
un Knowledge Engine completo.

## Sprint 28 membership admission

Membership is deterministic local-first admission before text interpretation.
Current state may be process-local or supplied through explicitly opened
SQLite. Default `Container` remains in-memory/no-I/O. Admission uses no model,
provider, or network and does not alter reasoning or downstream permissions.
This architecture is released at `sprint-28-complete`, peeled commit
`be22ffddda6d6961497c338caadf4c85e0fcb3ed`. Membership is not authentication
or action authorization; identities are not proof, trusted binding is not
durable membership, and `PermissionPolicy` remains downstream.

## Sprint 29 local authentication foundation

Released tag `sprint-29-complete` adds deterministic local, process-local,
nonpersistent proof authentication and explicit principal-to-actor mapping.
It precedes workspace selection and membership and leaves `PermissionPolicy`
as action authorization. This development/test/demo foundation makes no
model/provider/network calls and chooses no production credential technology.

## Sprint 31 governed durable action-permission release

The governed Sprint 31 release adds an optional durable local implementation of
the existing action-authorization boundary without changing local-first order.

Authorization still occurs after authentication, principal-to-actor mapping,
explicit workspace selection, and membership admission.

PermissionGrantRepository exposes only exact is_granted and append-only create.
RepositoryPermissionPolicy denies a missing grant, declared repository failure,
or invalid non-boolean repository result. Unexpected programming errors are not
silently converted into authorization outcomes.

SQLite schema v4 adds only:

action_permission_grants(actor_id, workspace_id, action)

All three values use exact binary/case-sensitive matching and the composite
primary key is (actor_id, workspace_id, action). Migration v3 -> v4 is additive,
uses BEGIN IMMEDIATE, and is rollback-safe.

Existing list, knowledge, membership, and principal/actor mapping state is
preserved.

Default Container composition remains no-I/O. Durable authorization requires
explicit repository injection. Configured grants and an injected permission
repository are mutually exclusive ownership choices.

The deterministic two-process proof demonstrates durable authorization success
plus fail-closed wrong-workspace, wrong-action, wrong-actor, and repository
failure scenarios with zero model, provider, readiness, network, and cognitive
fallback calls.

This implementation merged through PR #40 at
`9cad78ed22f0a6aef26eda0623d0f544cf65e5be` and is released at
`governed-sprint-31-complete`. Formal Sprint 31 governance closure was
subsequently completed at canonical checkpoint
`fa90defc44ad756a33f11e470105db57a440e201`.

## Sprint 32 authenticated local-command application gateway

Sprint 32 introduces a bounded, transport-independent application gateway for
authenticated local commands and one thin local-use HTTP adapter at
`POST /local/command`.

The application gateway does not create a new authentication, identity,
membership, permission, interpretation, local-resolution, or cognitive-routing
authority. It delegates exactly once to the existing
`AuthenticatedLocalCommandRoutingService`, which preserves the established
order:

authentication -> principal-to-actor mapping -> explicit workspace selection
-> membership admission -> deterministic text interpretation -> downstream
`PermissionPolicy` -> local capability resolution -> cognitive fallback only
when local insufficiency and explicit fallback authorization permit it.

`LocalCommandApplicationRequest` contains only the opaque authentication proof,
requested workspace, text, and explicit cognitive-fallback consent. The proof
is excluded from generic dataclass serialization and from request
representation. The HTTP transport uses a secret-aware proof field and unwraps
the secret exactly once when constructing the application request.

Application results expose only the closed public fields `success`, `route`,
`response`, and `error`. They do not expose principal, actor, membership,
repository, provider, routing, or other internal domain objects. The application
error taxonomy is closed and uses fixed public messages.

The local HTTP adapter validates its JSON body inside the adapter rather than
using automatic FastAPI request-body validation. Invalid JSON, malformed
transport input, missing required fields, forbidden extra fields, blank
workspace or text, invalid proof input, and non-boolean fallback values return
the controlled `invalid_request` envelope without exposing validation internals
or the authentication proof.

HTTP status ownership is explicit: successful local or cognitive results return
200; invalid requests return 400; access or local permission denial returns 403;
missing local knowledge returns 404; local knowledge conflict or unauthorized
cognitive fallback returns 409; local validation failure, controlled cognitive
failure, and service-resolution failure return 503; unexpected adapter
exceptions return a fixed sanitized 500 `internal_error` envelope.

`local_validation_failed` intentionally maps to HTTP 503 rather than 400 because
the existing local-resolution boundary uses that governed error for more than
caller-caused input validation, including declared local repository failure and
other terminal local-resolution failures.

The default `Container` composes exactly one
`LocalCommandApplicationGateway` from the already composed
`AuthenticatedLocalCommandRoutingService`. Default composition remains
fail-closed and performs no authentication attempt, SQLite open, durable
credential lookup, model invocation, provider readiness check, or network
request merely by constructing the container.

Sprint 32 does not introduce production authentication, durable credentials,
sessions, JWT, OAuth, device identity, RBAC, permission administration,
membership administration, principal-mapping administration, operational
SQLite runtime composition, cloud synchronization, public-Internet exposure,
CORS expansion, UI, desktop packaging, or automatic cognitive fallback.

The existing `/brain/think` and legacy `/knowledge` surfaces remain unchanged.
Sprint 32 does not claim that every existing HTTP route is authenticated. The
new `/local/command` endpoint is a bounded local-use development surface over
the authenticated local-command chain.

The local-first invariants remain unchanged: a sufficient deterministic local
result is terminal; local permission denial, local validation failure,
knowledge not-found, and knowledge conflict are terminal local outcomes; only
local insufficiency may proceed toward cognition; and cognition still requires
explicit fallback authorization. A supported deterministic local request must
not invoke model, provider, readiness, or network paths.

Sprint 32 architecture enforcement fixes these boundaries automatically:
`app/local_command` has exact topology and no transport/infrastructure/provider
coupling; the gateway owns exactly one authenticated-routing dependency; the
HTTP adapter cannot import lower authentication, membership, permission,
interpretation, local-resolution, coordinator, repository, or cognitive-engine
internals; the proof remains secret-aware; the HTTP status map is closed; the
adapter owns fixed unexpected-exception sanitization; and the pre-existing
brain, knowledge, main, and lifespan surfaces remain unchanged.

This section describes the Sprint 32 implementation state on its governed
implementation branch. It does not declare Sprint 32 merged, released, tagged,
or governance-closed; those statements require completion of the remaining
validation, independent review, merge, immutable release tag, and backup
lifecycle.

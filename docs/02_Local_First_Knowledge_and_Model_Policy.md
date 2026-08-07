# Local-First Knowledge and Model Policy

Version: 1.0
Status: Normative

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
fully released at the annotated tag `sprint-26-complete` and is the latest
completed tagged release.

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

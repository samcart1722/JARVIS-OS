# Sprint 43 — Evaluación de filtro local de metadatos visibles

Fecha: 2026-11-02. Estado: **PLANNING_ONLY / CANDIDATE_FOR_EVALUATION**.
El usuario autorizó iniciar planificación. Esta capacidad se propone ahora;
no existe aquí un alcance Sprint 43 previamente aprobado ni autorización de implementación.

## Base real y selección

Se consultaron `06_ROADMAP.md`, `05_TECHNICAL_DEBT.md`, el estado canónico,
Product North Star, Local-First Knowledge and Model Policy, reglas de dependencias
del Core y código UI de master `02557dc6a22c84913205b96c580f9752dc889d5e`.
El roadmap aún sitúa Sprint 41 en planificación y Sprint 42 como posible sucesor;
no contiene un compromiso Sprint 43 vigente. Esas secciones deben reconciliarse,
sin reinterpretarlas como autorización nueva.

La UI de master ya proyecta hasta 50 resúmenes BROWSE/BROWSE-AFTER con
`record_id`, `kind`, `key`, Prepare READ y Prepare next page. Se revisaron
`renderKnowledgeProjection`, `renderKnowledgeSummary`, `renderNextPageAction`,
`clearAllProjections` y su relación con Send. No se encontró un filtro de esa
página en la UI revisada. La deuda existente incluye capacidades mayores como
edit/delete y recuperación semántica; el filtro es una propuesta más acotada,
derivada de la experiencia local ya liberada y no una obligación del roadmap.

## Objetivo propuesto y beneficio

Permitir localizar visualmente un resumen por una parte literal de su ID o clave
en la página de metadatos que el usuario ya solicitó. Reduce el recorrido manual
de hasta 50 registros antes de preparar un READ. Funciona sin Qwen, Ollama, red
adicional ni regresión pendiente CORR03. La autorización existente sigue limitando
qué página se recibió y qué READ puede ejecutarse posteriormente.

## Alcance cerrado propuesto

1. Un campo y acción Clear filter, solo para proyecciones válidas BROWSE o
   BROWSE-AFTER. Etiqueta inequívoca: filtra únicamente esta página recibida.
2. Coincidencia literal por subcadena en `record_id` o `key`, sensible a mayúsculas,
   sin normalizar Unicode, recortar, tokenizar ni interpretar regex. Consulta vacía
   muestra todos. Propuesta de límite: 256 puntos de código; Unicode inválido o
   exceso produce error local, sin aplicar otro filtro ni modificar el editor.
3. Mantener el orden original. Mostrar `X de Y registros de esta página`, sin
   presentarlo como total del workspace. Diferenciar página vacía de filtro sin
   coincidencias; mantener la indicación original `truncated`.
4. Filtrar es solo presentación, sin solicitudes, repositorios, persistencia,
   proveedores, preparación de comando, modificación del editor o progreso guiado.
   Sin almacenamiento local/session/cookies ni analítica del texto del filtro.
5. Prepare READ conserva el ID original del resumen, no el texto visible ni su
   posición filtrada. Reutiliza el serializador y la invalidación existentes.
   Send sigue siendo explícito y vuelve a verificar los permisos vigentes.
6. Prepare next page conserva como anchor el último registro de la página
   original, aunque el filtro oculte ese registro o todas las filas. Nunca avanza
   automáticamente. Filtrar no consulta páginas anteriores ni siguientes.
7. Limpiar filtro restaura solo la vista. Nueva proyección, invalidación/limpieza
   de resultados o cambio de contexto descarta consulta y vista filtrada. Durante
   request pendiente se bloquea el control conforme a la UI existente; callbacks
   desprendidos de resultados anteriores no actúan. Etiquetas, teclado y estado
   accesible deben verificarse en aceptación nativa posterior.

Estas reglas son propuestas para estudio/contrato de Sprint 43. Si chocan con
una obligación congelada, se detiene el diseño y se decide otro alcance; no se
modifica un contrato congelado para acomodarlas.

## Dependencias y contratos que requieren estudio

| Dependencia o contrato | Pregunta que debe resolverse antes de implementar |
|---|---|
| Master actual y estado canónico reconciliado | Confirmar base funcional sin PR #84 ni cherry-pick de CORR03; revalidar drift |
| Proyección BROWSE/BROWSE-AFTER y permisos | Conservar esquema cerrado, metadata-only, máximo 50, orden y `truncated`; sin total/cursor nuevo |
| Interpretación READ/BROWSE/BROWSE-AFTER | Prepare debe producir exactamente la gramática existente y el anchor original |
| Contratos congelados Sprint 40 y 41 | Preservar correlación guiada, invalidación, editor exacto, preparación pura y Send |
| Contrato Sprint 42 + Amendment 01 | Estudiar compatibilidad futura sin depender del código experimental ni habilitarlo |
| ADR Local Interactive Runtime and Loopback UI | Mantener transporte/CSRF/Host/Origin, cero solicitudes al filtrar y frontera del runtime |
| Local-First Policy / Cognitive Core Dependency Rules | Presentación sin modelo, sin dependencias hacia infraestructura desde el Core |
| Nuevo contrato de comportamiento Sprint 43 | Aprobar límites, Unicode, accesibilidad, reset, estados y criterio de aceptación; aún no existe |

No depende de INF-HARNESS-01 ni S42-AD-01/02 para planificar o validar de forma
focal una UI independiente. La ejecución futura exige su propia ruta de pruebas
aceptada; esto no autoriza reutilizar un harness bloqueado ni omitir checks aplicables.

## Archivos y módulos candidatos

| Archivo | Papel candidato |
|---|---|
| `app/api/static/local_ui/index.html` | Campo, clear, ayuda y estado accesible |
| `app/api/static/local_ui/app.js` | Vista derivada de resúmenes e invalidación; estudiar funciones citadas, sin cambiar serializadores |
| `app/api/static/local_ui/styles.css` | Ajustes mínimos a controles/filas ocultas si fueran necesarios |
| `tests/browser/local_knowledge_browse.js` | Cobertura de página, metadatos y READ original |
| `tests/browser/local_knowledge_browse_after.js` | Anchor original y continuidad bajo filtro |
| `tests/browser/local_guided_capture_recall_action.js` | Compatibilidad de correlación/preparación/reset |
| `tests/unit/api/test_local_interactive_ui.py` | Estructura servida y paridad con intérprete, según contrato final |
| Nuevo documento de comportamiento Sprint 43 | Solo tras aprobar el candidato y autorizar su ciclo documental |

La lista es de estudio, no una allowlist de implementación ya autorizada.
No se prevén cambios de backend, Core, modelos HTTP, storage, permisos ni esquema.

## Riesgos y pruebas propuestas

| Riesgo | Prueba útil para resolverlo |
|---|---|
| Confundir filtro con búsqueda global | Página con `truncated=true`, cero coincidencias locales, texto y total limitados a la página |
| Cambiar anchor o reordenar resultados | Filtro oculta último registro/todos; Prepare next page usa ID final original y orden estable |
| READ equivocado o botón obsoleto | IDs con Unicode/delimitadores, cambio de proyección, callbacks desprendidos y clics repetidos; ID original y serialización existente |
| Filtrar ejecuta o altera editor/progreso | Contadores de requests/provider y snapshots de editor/correlación antes/después: cero cambios salvo vista |
| Filtrado Unicode ambiguo o inyección | Subcadena exacta, caja, compuesto/descompuesto, astrales, límites, surrogate inválido, HTML literal mediante textContent |
| Pérdida de acceso por teclado o estado confuso | Tabulación/foco, etiqueta, contador, Clear, vacíos y pending en sesión nativa aislada autorizada |
| Regresión del flujo liberado | Harnesses BROWSE/BROWSE-AFTER/S40/S41 aplicables; paridad real de comandos preparados; denegación/revocación READ en Send |

No se escriben ni ejecutan pruebas en esta planificación. Tras aprobar alcance:
pruebas focales de comportamiento, regresión afectada y sintaxis/lint apropiados;
aceptación nativa independiente con datos sintéticos. Una prueba DOM no se reporta
como Edge, y los resultados Sprint 42 no prueban esta capacidad.

## Criterios propuestos de aceptación

- Todos los casos de literalidad, límites, Unicode, vacíos y reset cumplen el
  contrato nuevo aprobado, con metadatos originales, sin datos adicionales.
- Filtrar/limpiar produce cero solicitudes y cero cambios de editor, comandos,
  autorización, persistencia, guía o proveedores. Se conserva el orden y el total
  de la página original como denominador; no se inventa un total global.
- Prepare READ y next page mantienen IDs/anchor exactos y paridad del intérprete;
  botones obsoletos/pending no actúan y no se ejecuta nada automáticamente.
- Sin Ollama disponible, los flujos deterministas y el filtro siguen operando.
  Pruebas y aceptación se realizan sobre master/base aprobada sin integrar #84.
- Regresión aplicable, revisión independiente y evidencia nativa del cambio PASS;
  cero modificaciones de contratos congelados, backend, esquema o autoridad.

## Trabajo explícitamente excluido

Inferencias, aceptación CORR03, reparación MODEL05, construcción del harness o
asignar todo el backlog Sprint 42; integración/cierre del PR #84; búsqueda global,
semántica/fuzzy, ranking, normalización, filtros del servidor, multi-página o historial;
contenido/provenance adicional, edición/eliminación de conocimiento, caché o drafts
persistentes, clipboard/exportación, nuevas intenciones, voz, agentes, Hermes,
Spatial, HealthBridge, autenticación o permisos nuevos. Tampoco merge/release.

## Condiciones mínimas para iniciar implementación

Aprobar explícitamente este candidato o reemplazarlo; estudiar y aprobar el nuevo
contrato sin cambiar los congelados; reconciliar base canónica y confirmar una
rama/worktree nueva separada de los cuatro históricos; acordar allowlist y ruta
de validación segura propia; obtener autorización expresa de implementación.
La aprobación integral Sprint 42 no es prerrequisito de una mejora independiente.
Este documento no satisface por sí solo ninguna de esas decisiones futuras.

**HARD STOP: planificación terminada; cero funcionalidad Sprint 43 implementada.**

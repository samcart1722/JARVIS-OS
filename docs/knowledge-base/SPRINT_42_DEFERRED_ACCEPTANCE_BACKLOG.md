# Sprint 42 — Backlog diferido de integración asistida por modelo

Fecha: 2026-11-02. Estado global: **ACCEPTANCE_DEBT_OPEN**.
Planificación de cartera; sin sprint, responsable ni fecha de ejecución asignados.
El cierre administrativo parcial no satisface estos criterios ni autoriza su ejecución.

## Referencias y restricciones comunes

Fuente original: informes MODEL04/MODEL05, CORR03-A, R1, RECOVERY1/2/3 y
E2-HARNESS-AUDIT. Las rutas y SHA-256 constan en `evidence/evidence-index.json`
del paquete de revisión externo. GitHub: [PR #84](https://github.com/samcart1722/JARVIS-OS/pull/84).
La tabla completa de cuatro commits/ramas está en el [registro de cierre](SPRINT_42_PARTIAL_CLOSURE_RECORD.md).

Base funcional del PR: `64424733989e8a73544b83150eb437ab5970fc64`.
CORR01: `d791abd570ed1cbdfbe72c248b7aca853a63e78e`.
MODEL04/MODEL05 y Python histórico se vinculan a CORR02:
`7ee4e48d0a043e43c40c94ccb6dd40647734d66c`, rama `fix/sprint-42-e2-corr02`.
La reanudación del prompt corregido parte de CORR03:
`5be476a6f591853a6fe257326a91e1e161cba29e`, rama `fix/sprint-42-e2-corr03`.
No se sustituyen estas identidades con evidencia de otro commit.

Restricciones para todas las entradas: no acceder, enumerar, copiar, importar,
recopilar, ejecutar ni hacer controles negativos sobre `tests/unit/reasoning`.
Los controles usan sustitutos sintéticos. Preservar los worktrees y los contratos
Sprint 40/41/42 + Amendment 01. Sin datos reales, secretos o bases de usuario.
Modelo solo opcional, local y bajo autorización; sin Send automático, ampliación
de autoridad, retries ocultos, reparación de respuestas ni fallback cloud.
**Prohibidos despliegue y activación permanente sin aceptación y autorización.**

Ningún gate podrá declararse aceptado o PASS sin ejecutar sus pruebas autorizadas y conservar evidencia verificable correspondiente a dicho gate. Los resultados históricos, pruebas focales o controles realizados sobre otro commit no sustituyen la evidencia de aceptación requerida.

## Disposición de evidencia independiente CORR03-B

`E2_CORR03_B_APPROVED` identifica la revisión independiente técnica de CORR03:
aprobación histórica reportada, informe original no localizado y procedencia
no verificable con los artefactos disponibles. Ruta original y SHA-256 original:
desconocidos. Aprobación documentalmente certificada: **NO**. Equivalencia
documental: no demostrada. Deuda de evidencia: **ABIERTA**. No se altera el
resultado reportado ni se afirma que la revisión nunca ocurrió o esté verificada.

El registro administrativo de PARTIAL_CLOSURE / ACCEPTANCE_DEBT_OPEN puede
tramitarse con la excepción declarada, revisión independiente documental y
autorización Git separada. La aceptación técnica CORR03 sigue pendiente de
evidencia verificable y de sus gates; la integración o liberación funcional
permanece sin autorización. La excepción no sustituye aprobación técnica.

Remediación futura, sin ejecución ahora:

1. Recuperación: localizar posteriormente el original y verificar autenticidad,
   procedencia, alcance, archivos y commit revisados.
2. Nueva revisión: si no se recupera, realizar una revisión independiente nueva
   de CORR03 con identificador propio, fecha efectiva, commit exacto, evidencia
   reproducible y veredicto independiente; no atribuirle retroactivamente el
   resultado histórico ni presentarla como el informe original.

Ambas alternativas conservan los requisitos pendientes de Python integral,
validación semántica y Edge cuando corresponda, además de los demás gates.

## INF-HARNESS-01 — Línea separada de infraestructura aislada

Estado: DESIGN_READY / IMPLEMENTATION_AND_ACCEPTANCE_PENDING. No es una función
Sprint 43 ni una razón para modificar el núcleo. Evidencia original:
`E2-CORR03-R1-RECOVERY3-20261102-88d2fa61/REPORT.md` y
`E2-HARNESS-AUDIT-20261102-6df928b1/REPORT.md`.

Problema: audit hooks del padre no son frontera de seguridad del SO y no se
heredan automáticamente a nuevos intérpretes. NUL se resolvió en controles
acotados; la supervisión integral de descendientes sigue sin demostrarse.
Los fallos del harness no se atribuyen a CORR03 sin evidencia causal.

La allowlist y el manifiesto de 129 archivos constituyen una referencia histórica, no una allowlist completa certificada. Su completitud y procedencia, incluidas las fixtures y los imports de los subárboles autorizados, deberán verificarse y cerrarse antes de H1/H2 y de cualquier ejecución H3. Si falta procedencia o cierre verificable, el estado permanecerá BLOCKED y no se ejecutará una regresión exploratoria.

Reanudación: aprobar recursos y responsables para H1/H2 por separado. Diseño
preferido registrado: VM Windows desechable en host Hyper-V autorizado, snapshot
de allowlist positiva, sin NIC ni carpetas host compartidas, herramientas selladas,
política verificable de archivos/dispositivos/red incluyendo loopback y descendientes.
La auditoría no verificó disponibilidad/licencia del host e imagen adicionales.
No convertir el snapshot solo o el hook Python en garantía de aislamiento.

Aceptación: H1 entrega imagen, lock de herramientas, cierre de fixtures y exportador;
H2 demuestra contención de padres/hijos/nietos y helper nativo con recursos
sintéticos, NUL real frente a archivo ordinario, permisos y red del SO, cwd y
spawn compatibles; revisor independiente aprueba antes de LUXIOM. La exportación
debe ser cerrada y sin enlaces. Si falta una garantía, HARNESS_BLOCKED sin pytest.
No iniciar RECOVERY4 ni ampliar excepciones durante la regresión.

H3 será la regresión separadamente autorizada que consume S42-AD-01. La
infraestructura se versionará en una ubicación/rama propia; no se construye aquí.

## S42-AD-01 — Regresión Python integral posterior a CORR03

Estado: BLOCKED_BY_INF-HARNESS-01. Evidencia original: XML CORR02-R1, informes
CORR03-R1/RECOVERY y `results-summary.json` de RECOVERY3.
La última condición registrada es `NOT_RUN_CONDITION_NOT_MET`; 28 casos nuevos
sin aceptación integral. Los 103 focales no sustituyen la regresión completa.

Reanudación: INF-HARNESS-01 H2 aprobado, commit/contratos intactos, manifiesto y
fixtures completos sellados, entorno y único intento autorizados expresamente.
Mantener Python 3.14.7 y versiones/entorno aceptados o revisar la equivalencia
antes de ejecutar; conservar conftest y pruebas CLI obligatorias sin desactivarlas.

Aceptación: ejecutar las 3,939 identidades históricas y las 28 nuevas exactamente
una vez, verificar multiconjuntos de collected y reportes, todas PASS. Un total
aritmético de 3,967 no basta. Sin errores, omisiones, skips/deselections favorables
ni cambios de tests para acomodar el runner. Manifiesto actual de 129 archivos
es una referencia sellada del gate anterior, sujeto a revisión de cierre de fixtures.
Conservar logs, XML, límites de observabilidad e integridad antes/después.

## S42-AD-02 — Validación semántica real CORR03

Estado: NOT_RUN. Evidencia: prompt/patch CORR03-A y MODEL04/MODEL05 sobre CORR02.
Depende de S42-AD-01 y de un entorno de inferencia aislado aceptado para ese gate.
El harness de regresión sin red no autoriza conectar Ollama; su perfil de
inferencia requiere revisión propia y loopback acotado en la misma máquina.

Reanudación: autorización expresa del modelo/digest, presupuesto, recursos y
conjunto con criterios previos; usar proveedor, parser, grounding, validator y
servicio reales, sin simulaciones o HTTP directo que eluda el adaptador.
Modelo histórico de referencia: `qwen3.5:4b-q4_K_M`, digest
`d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
Verificar identidad en la reanudación, sin descargas o sustituciones automáticas.

Aceptación: registrar por caso intención/campos esperados, salida literal,
resultado funcional, abstención, límites y latencias; conservar timeout de proveedor
30s y deadline UI 35s donde aplique. Demostrar cero autoridad previa a Send,
sin reintentos/repair. Separar casos conocidos de conjunto reservado y abstención
de extracción útil. Revisión independiente decide aptitud; no generalizar MODEL04.

## S42-AD-03 — Fallos funcionales MODEL05

Estado: CHANGES_REQUIRED / CORRECTION_EFFECT_UNVERIFIED. Depende de S42-AD-02.
Evidencia original: `E2-MODEL05-20261101-mvyae63o/INFORME_E2_MODEL05.md`,
resultados G06/G11/G12 y prompt CORR03. La aprobación histórica de la revisión
técnica solo está reportada; no está documentalmente certificada. Su deuda se
remedia por las alternativas CORR03-B anteriores, sin bloquear por sí sola el
registro administrativo ni aceptar la funcionalidad.

Reanudación: criterios sellados para G06 y parciales, más variaciones nuevas.
Aceptación: G06 extrae `baterías`, sin incluir `Suma`; comprobar palabras de
apariencia verbal que sí forman parte del item. G11/G12 deben evaluarse con
campos literales parciales cuando identificables, sin inventar destino; un rechazo
seguro puede respetar seguridad y aun dejar utilidad sin demostrar. El rechazo
no se cuenta como corrección de extracción. Si persiste una brecha funcional,
mantener CHANGES_REQUIRED o registrar una decisión de alcance explícita, sin
reescribir los contratos congelados ni declarar PASS por porcentaje agregado.

## S42-AD-04 — Aceptación nativa Edge

Estado: NOT_ACCEPTED. Depende de S42-AD-01/02/03 y aprobación específica del gate.
Evidencia original: los requisitos E2 del PR #84; DOM/Node 10,640 no son prueba
nativa. No reutilizar aceptación Sprint 40/41 como aceptación Sprint 42.

Reanudación: commit/modelo exactos aceptados, entorno Windows/Edge aislado,
base SQLite sintética, actor/workspace/permisos explícitos, perfil Edge nuevo.
Aceptación: foco, teclado, suspensión y recuperación; carreras y obsolescencia;
timeouts, cold/warm latency y RAM; OFF/default y rechazo; cero autoridad pre-Send;
Send positivo/negativo/denegado/revocado con texto exacto y cuatro familias.
Cancelación lógica no prueba terminación física inmediata del worker/HTTP.
Todo arranque Edge o inferencia requiere la autorización futura correspondiente.

## S42-AD-05 — Integración y cierre Git de la funcionalidad

Estado: DEFERRED / NOT_AUTHORIZED. Depende de las aceptaciones anteriores,
revisión independiente final y criterios de release aplicables.
Evidencia: PR #84 draft en `6442473…`; CORR01/02/03 solo locales; cuatro HEAD
preservados. El cierre administrativo parcial no cierra este trabajo.

Reanudación funcional: recuperar y verificar el informe original CORR03-B o
realizar la nueva revisión independiente descrita arriba, completar las demás
aceptaciones aplicables y verificar otra vez head/base remotos y contrato combinado.
Revisar cambios y evidencia; definir integración aislada sin alterar los cuatro
worktrees. La excepción administrativa no satisface estas condiciones técnicas.
Aceptación: autorización separada para publicar las correcciones, actualizar
el PR, marcar ready, integrar y completar validación/release según corresponda.
No anticipar que commit, push, merge, tag, backup/recovery o release ya ocurrieron.
La integración solo documental tiene un plan separado y no satisface esta entrada.

## Regla de planificación

Sprint 43 puede evaluar una mejora determinista independiente con base en master,
sin consumir este backlog. Infraestructura, integración asistida por modelo y
capacidades locales son líneas distintas. Asignar sprint/owner/fecha exige una
decisión posterior; no se arrastra toda la deuda por defecto al siguiente sprint.

**HARD STOP.**

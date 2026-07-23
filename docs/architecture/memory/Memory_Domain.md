# Memory Domain
## JARVIS-OS
### Documento de Arquitectura

Versión: 1.0
Sprint: 31

---

# 1. Propósito

El dominio de memoria define las entidades fundamentales utilizadas por el sistema cognitivo de JARVIS.

Estas entidades representan el lenguaje común utilizado por todos los componentes del Memory Pipeline.

Ningún componente debe intercambiar datos utilizando estructuras improvisadas.

Toda comunicación debe realizarse mediante objetos del dominio.

---

# 2. Filosofía

El dominio representa conocimiento.

No representa bases de datos.

No representa APIs.

No representa el modelo del LLM.

Representa únicamente conceptos cognitivos.

---

# 3. Entidades del dominio

El sistema utilizará las siguientes entidades principales.

---

## MemoryFact

Representa un conocimiento individual.

Ejemplos

```
Soy médico.
```

```
Mi color favorito es azul.
```

```
Estoy desarrollando JARVIS.
```

Responsabilidades

- representar un único conocimiento
- permanecer independiente del almacenamiento
- ser inmutable siempre que sea posible

Atributos actuales

- key
- value

Atributos futuros

- id
- category
- key
- value
- confidence
- source
- created_at
- updated_at
- expires_at

---

## RetrievedMemory

Representa una memoria recuperada para una conversación.

No toda memoria almacenada será utilizada.

RetrievedMemory representa únicamente aquellas seleccionadas por el Retriever.

Puede incluir información adicional utilizada durante el ranking.

Ejemplo

- score
- reason
- memory

---

## MemoryCategory

Clasifica el tipo de conocimiento.

Categorías iniciales

Facts

Preferences

Goals

Relationships

Dynamic State

La arquitectura permitirá incorporar nuevas categorías.

---

## MemorySource

Describe el origen de una memoria.

Ejemplos

RuleExtractor

SemanticExtractor

Manual

Imported

Future Learning

El origen permitirá mejorar la trazabilidad.

---

## MemoryConflict

Representa un conflicto detectado entre memorias.

Ejemplo

Anterior

```
Vivo en Tegucigalpa.
```

Nueva

```
Ahora vivo en San Pedro Sula.
```

El conflicto será evaluado por el Conflict Resolver.

---

## MemoryQuery

Representa una solicitud de recuperación.

Ejemplo

```
¿Qué sabe JARVIS sobre el usuario?
```

o

```
Recuperar memorias relacionadas con programación.
```

Debe permitir futuras estrategias de recuperación.

---

## MemoryResult

Representa el resultado final del proceso de recuperación.

Puede incluir

- memorias
- score total
- estadísticas
- información diagnóstica

---

# 4. Relaciones

```
MemoryQuery
      │
      ▼
MemoryRetriever
      │
      ▼
RetrievedMemory
      │
      ▼
MemoryFact
      │
      ▼
MemoryCategory
      │
      ▼
MemorySource
```

Los conflictos serán representados mediante MemoryConflict.

---

# 5. Invariantes

Un MemoryFact representa únicamente un conocimiento.

Un MemoryFact no puede pertenecer simultáneamente a múltiples categorías.

Una memoria recuperada siempre referencia un MemoryFact.

Toda memoria debe tener un origen.

Toda memoria debe poseer una clave válida.

Toda memoria debe poseer un valor válido.

---

# 6. Ciclo de vida

Creación

↓

Clasificación

↓

Validación

↓

Persistencia

↓

Recuperación

↓

Actualización

↓

Archivado o Expiración

---

# 7. Comunicación entre componentes

Los componentes del pipeline nunca deben compartir estructuras arbitrarias.

La comunicación se realizará exclusivamente mediante entidades del dominio.

Esto garantiza

- desacoplamiento
- mantenibilidad
- extensibilidad
- facilidad de pruebas

---

# 8. Evolución

El dominio está diseñado para crecer.

Ejemplos futuros

MemoryEpisode

MemoryProcedure

MemorySkill

MemoryPreference

MemoryGoal

MemoryRelationship

MemoryEmotion

MemoryBelief

KnowledgeNode

KnowledgeEdge

Todos deberán integrarse sin romper compatibilidad.

---

# 9. Principios

El dominio es independiente.

No depende del LLM.

No depende de FastAPI.

No depende de SQLAlchemy.

No depende del almacenamiento.

No depende de Redis.

No depende del proveedor de IA.

El dominio representa únicamente conceptos del sistema cognitivo.

---

# 10. Filosofía Final

El conocimiento es el activo más importante de JARVIS.

El dominio existe para representar ese conocimiento de forma consistente, estable y extensible.

Todo el sistema cognitivo debe construirse alrededor de estas entidades.

El dominio debe permanecer simple, expresivo y ajeno a cualquier detalle de infraestructura.
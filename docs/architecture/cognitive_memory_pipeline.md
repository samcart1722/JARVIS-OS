# Cognitive Memory Pipeline
Version: 1.0

---

# Objetivo

El Cognitive Memory Pipeline es el componente responsable de coordinar todo el ciclo de vida de la memoria dentro de JARVIS-OS.

Su responsabilidad no es almacenar información ni analizar lenguaje natural. Su única función consiste en orquestar los componentes especializados del sistema de memoria.

El Pipeline representa el punto único de entrada para cualquier operación relacionada con memoria.

---

# Principios de Diseño

El diseño sigue los principios de:

- Domain Driven Design (DDD)
- Clean Architecture
- SOLID
- Dependency Injection
- Single Responsibility Principle

Cada componente realiza exactamente una tarea.

El Pipeline nunca implementa lógica de negocio específica.

Su función consiste únicamente en coordinar el flujo de trabajo.

---

# Arquitectura General

```
                 remember()

                      │
                      ▼

              MemoryExtractor

                      │
                      ▼

              MemoryValidator

                      │
                      ▼

             MemoryClassifier

                      │
                      ▼

             MemoryRepository

                      │
                      ▼

                 MemoryFact
```

```
                  recall()

                      │
                      ▼

             MemoryRepository

                      │
                      ▼

             MemoryRetriever

                      │
                      ▼

               MemoryRanker

                      │
                      ▼

                MemoryResult
```

---

# Componentes

## MemoryExtractor

Responsabilidad:

Transformar una entrada de texto en uno o más objetos MemoryFact.

No almacena información.

No valida.

No clasifica.

No consulta el repositorio.

---

## MemoryValidator

Responsabilidad:

Determinar si una memoria cumple los requisitos mínimos para ser persistida.

Ejemplos:

- contenido vacío
- contenido demasiado corto
- contenido inválido

No modifica la memoria.

No la almacena.

Devuelve únicamente un valor booleano.

---

## MemoryClassifier

Responsabilidad:

Asignar metadatos semánticos a una memoria.

Ejemplos futuros:

- categoría
- etiquetas
- importancia
- prioridad
- nivel de confianza

En la versión 1 el clasificador es transparente.

Simplemente devuelve la misma memoria.

---

## MemoryRepository

Responsabilidad:

Persistencia.

No realiza clasificación.

No valida.

No interpreta lenguaje.

Su única responsabilidad consiste en almacenar y recuperar memorias.

---

## MemoryRetriever

Responsabilidad:

Aplicar estrategias de recuperación sobre las memorias obtenidas del repositorio.

Ejemplos futuros:

- recuperación semántica
- búsqueda híbrida
- búsqueda vectorial
- recuperación contextual

En V1 actúa como una capa simple.

---

## MemoryRanker

Responsabilidad:

Ordenar las memorias recuperadas.

Ejemplos futuros:

- relevancia
- similitud
- prioridad
- confianza
- recencia

---

# Flujo remember()

## Paso 1

El usuario proporciona contenido.

```
str
```

---

## Paso 2

El extractor genera una colección de MemoryFact.

```
tuple[MemoryFact, ...]
```

---

## Paso 3

Cada memoria es validada.

Las memorias inválidas son descartadas.

El Pipeline no lanza excepciones por memorias inválidas.

---

## Paso 4

Cada memoria válida pasa por el clasificador.

El clasificador puede enriquecer la memoria.

Nunca debe eliminar información existente.

---

## Paso 5

Cada memoria clasificada es almacenada mediante MemoryRepository.

---

## Paso 6

El Pipeline devuelve únicamente las memorias persistidas exitosamente.

```
tuple[MemoryFact, ...]
```

---

# Flujo recall()

## Paso 1

El usuario proporciona un MemoryQuery.

---

## Paso 2

El Pipeline solicita resultados al repositorio.

```
MemoryRepository.search()
```

---

## Paso 3

El retriever aplica estrategias de recuperación.

---

## Paso 4

El ranker ordena los resultados.

---

## Paso 5

El Pipeline devuelve un MemoryResult.

---

# Manejo de Errores

## Error de validación

No genera excepción.

La memoria simplemente no se persiste.

---

## Error de persistencia

Debe propagarse.

El Pipeline no oculta errores del repositorio.

---

## Error del clasificador

Debe propagarse.

El clasificador representa una dependencia crítica.

---

## Error del extractor

Debe propagarse.

Si no es posible extraer memorias no existe flujo válido.

---

# Invariantes

Siempre deben cumplirse las siguientes reglas:

- El Pipeline nunca modifica directamente el repositorio.
- Cada componente posee una única responsabilidad.
- Los componentes nunca se llaman entre sí.
- Toda coordinación ocurre exclusivamente dentro del Pipeline.
- El repositorio nunca clasifica memorias.
- El clasificador nunca persiste memorias.
- El extractor nunca consulta el repositorio.
- El validator nunca modifica objetos.
- El ranker nunca accede a almacenamiento.

---

# Escalabilidad

La arquitectura permite reemplazar cualquier componente sin modificar el resto del sistema.

Ejemplos:

Extractor

```
DefaultExtractor

↓

LLMExtractor
```

Validator

```
DefaultValidator

↓

ClinicalValidator
```

Classifier

```
DefaultClassifier

↓

OllamaClassifier

↓

GPTClassifier
```

Repository

```
InMemoryRepository

↓

SQLiteRepository

↓

PostgreSQLRepository

↓

VectorRepository
```

Retriever

```
DefaultRetriever

↓

SemanticRetriever

↓

HybridRetriever
```

Ranker

```
DefaultRanker

↓

VectorRanker

↓

HybridRanker
```

---

# Responsabilidades del Pipeline

El Pipeline es responsable únicamente de:

- coordinar el flujo;
- invocar los componentes en el orden correcto;
- propagar errores críticos;
- devolver resultados consistentes.

El Pipeline nunca debe contener reglas de negocio específicas de memoria.

Toda lógica especializada pertenece a los componentes individuales.

---

# Evolución

## Versión 1

- Extractor simple
- Validator simple
- Clasificador transparente
- Repositorio en memoria
- Recuperación básica
- Ranking básico

---

## Versión 2

- Clasificación mediante LLM
- Etiquetado automático
- Resumen de memorias
- Deduplicación
- Recuperación semántica
- Ranking híbrido

---

## Versión 3

- Base vectorial
- Memoria episódica
- Memoria semántica
- Consolidación automática
- Aprendizaje continuo
- Expiración inteligente de memorias
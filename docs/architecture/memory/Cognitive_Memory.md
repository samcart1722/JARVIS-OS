# Cognitive Memory
## JARVIS-OS
### Documento de Arquitectura

Versión: 1.0
Sprint: 31

---

# 1. Visión

La memoria cognitiva de JARVIS no es un simple almacén de datos.

Su propósito es construir, mantener y evolucionar un modelo interno del usuario a partir de las conversaciones.

Cada interacción puede generar nuevos conocimientos, actualizar conocimientos existentes o descartar información obsoleta.

La memoria debe permitir que JARVIS se vuelva más útil con el tiempo sin perder consistencia.

---

# 2. Objetivos

La memoria cognitiva debe ser capaz de:

- Aprender información nueva.
- Recordar hechos persistentes.
- Diferenciar información temporal de permanente.
- Actualizar conocimientos cuando cambian.
- Resolver conflictos entre recuerdos.
- Recuperar únicamente la información relevante.
- Explicar por qué recuerda determinada información.

---

# 3. Principios

## Persistencia

Los hechos importantes permanecen mientras no sean reemplazados.

Ejemplo:

Soy médico.

---

## Evolución

Una memoria puede cambiar.

Ejemplo:

Antes:

Vivo en Tegucigalpa.

Después:

Ahora vivo en San Pedro Sula.

La memoria anterior debe actualizarse.

---

## Relevancia

No toda la información merece almacenarse.

Debe existir un proceso de selección.

---

## Consistencia

Dos recuerdos no deben contradecirse.

Cuando exista conflicto se resolverá mediante reglas de prioridad.

---

## Explicabilidad

JARVIS debe poder justificar una respuesta utilizando las memorias recuperadas.

---

# 4. Categorías de memoria

## Facts

Información objetiva.

Ejemplos

- profesión
- nombre
- ciudad
- idioma
- edad

Persistencia:

Alta.

---

## Preferences

Preferencias personales.

Ejemplos

- lenguaje favorito
- editor favorito
- comida favorita

Persistencia:

Media.

---

## Goals

Objetivos del usuario.

Ejemplos

- construir JARVIS
- desarrollar HealthBridge
- lanzar una empresa

Persistencia:

Alta.

---

## Relationships

Personas importantes.

Ejemplos

- esposa
- hijos
- socios

Persistencia:

Alta.

---

## Dynamic State

Información temporal.

Ejemplos

- estoy enfermo
- estoy cansado
- estoy de vacaciones

Persistencia:

Baja.

Debe expirar automáticamente.

---

# 5. Modelo de memoria

Cada recuerdo será representado mediante un MemoryFact.

Versión inicial:

- key
- value

Versión futura:

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

# 6. Ciclo de vida

Conversación

↓

Extracción

↓

Clasificación

↓

Validación

↓

Persistencia

↓

Recuperación

↓

Uso por el modelo

---

# 7. Extracción

La memoria utilizará dos mecanismos.

## Rule Extractors

Detectan patrones conocidos.

Ejemplo

Soy médico.

---

## Semantic Extractor

Detecta hechos no cubiertos por reglas específicas.

Ejemplo

Mi color favorito es azul.

No requiere un extractor dedicado.

---

# 8. Clasificación

Cada memoria recibirá una categoría.

Facts

Preferences

Goals

Relationships

Dynamic State

---

# 9. Resolución de conflictos

Si una memoria nueva contradice una anterior:

Ejemplo

Antes

Vivo en Tegucigalpa.

Después

Ahora vivo en San Pedro Sula.

La memoria anterior será reemplazada.

Toda actualización conservará un historial.

---

# 10. Recuperación

La recuperación no debe devolver toda la memoria.

Debe devolver únicamente la información relevante para el contexto actual.

El proceso utilizará:

- Retriever
- Ranker
- Sorter

---

# 11. Priorización

La prioridad dependerá de:

- categoría
- confianza
- recencia
- frecuencia de uso
- relevancia contextual

---

# 12. Memoria temporal

Las memorias temporales podrán expirar.

Ejemplos

Hoy estoy enfermo.

Hoy estoy cansado.

No deben permanecer indefinidamente.

---

# 13. Futuro

La arquitectura permitirá incorporar:

- aprendizaje automático
- embeddings
- recuperación semántica
- memoria episódica
- memoria procedimental
- memoria autobiográfica

sin modificar la arquitectura principal.

---

# 14. Filosofía

JARVIS no almacena conversaciones.

Construye conocimiento.

Cada conversación modifica gradualmente un modelo interno coherente del usuario.

La memoria existe para comprender mejor al usuario, no para acumular texto.
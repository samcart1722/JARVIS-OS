# Component Contracts
## JARVIS-OS
### Documento de Arquitectura

Versión: 1.0
Sprint: 31

---

# 1. Propósito

Este documento define los contratos utilizados por los componentes del Cognitive Memory Engine.

Un contrato especifica qué responsabilidad tiene un componente, qué recibe como entrada, qué devuelve como salida y qué comportamiento garantiza.

Los contratos permiten que múltiples implementaciones puedan coexistir sin modificar el resto del sistema.

---

# 2. Filosofía

Los componentes no deben depender de implementaciones concretas.

Cada componente debe comunicarse exclusivamente mediante contratos claramente definidos.

El objetivo es garantizar:

- desacoplamiento
- extensibilidad
- mantenibilidad
- facilidad de pruebas
- reemplazo transparente de implementaciones

---

# 3. Principios

Cada contrato debe representar una única responsabilidad.

Los contratos no contienen lógica.

Los contratos no conocen detalles de infraestructura.

Los contratos no dependen del proveedor de IA.

Los contratos son estables.

Las implementaciones evolucionan.

---

# 4. Memory Extractor

Responsabilidad

Extraer conocimiento desde lenguaje natural.

Entrada

Texto normalizado.

Salida

Lista de MemoryFact.

Garantías

- nunca modifica memorias existentes
- no persiste información
- no clasifica memorias
- únicamente extrae conocimiento

Implementaciones previstas

- ProfessionExtractor
- ProjectExtractor
- SemanticExtractor
- Future Extractors

---

# 5. Memory Classifier

Responsabilidad

Asignar una categoría a un MemoryFact.

Entrada

MemoryFact.

Salida

MemoryCategory.

Garantías

- no modifica el contenido del MemoryFact
- únicamente determina su categoría

Implementaciones futuras

- RuleClassifier
- LLMClassifier

---

# 6. Conflict Resolver

Responsabilidad

Resolver contradicciones entre memorias.

Entrada

Memoria existente.

Memoria nueva.

Salida

Resolución del conflicto.

Posibles resultados

- Replace
- Update
- Ignore
- Merge

Garantías

Nunca persiste cambios.

Únicamente decide cómo resolver el conflicto.

---

# 7. Memory Validator

Responsabilidad

Verificar la validez de una memoria.

Entrada

MemoryFact.

Salida

ValidationResult.

Debe comprobar

- estructura válida
- categoría válida
- clave válida
- valor válido
- confianza mínima

No modifica memorias.

---

# 8. Memory Ranker

Responsabilidad

Ordenar memorias según su importancia.

Entrada

Lista de RetrievedMemory.

Salida

Lista ordenada.

Factores posibles

- relevancia
- confianza
- categoría
- recencia
- frecuencia de uso

No elimina memorias.

Solo modifica el orden.

---

# 9. Memory Retriever

Responsabilidad

Recuperar memorias relevantes.

Entrada

MemoryQuery.

Salida

Lista de RetrievedMemory.

Debe minimizar el contexto enviado al LLM.

Nunca devuelve información innecesaria.

---

# 10. Context Builder

Responsabilidad

Construir el contexto final para el modelo.

Entrada

- conversación reciente
- memorias recuperadas
- instrucciones del sistema

Salida

Contexto listo para el LLM.

Garantías

Debe producir un contexto compacto, coherente y consistente.

---

# 11. Memory Repository

Responsabilidad

Persistir memorias.

Operaciones principales

- guardar
- actualizar
- eliminar
- buscar

El repositorio no toma decisiones cognitivas.

Únicamente almacena información.

---

# 12. Memory Intelligence

Responsabilidad

Coordinar todo el proceso de aprendizaje.

Es el orquestador principal del pipeline.

Responsabilidades

- ejecutar extractores
- combinar resultados
- invocar clasificadores
- resolver conflictos
- validar memorias
- enviar memorias al repositorio

No implementa reglas de negocio específicas.

Coordina componentes.

---

# 13. Dependencias Permitidas

```
Memory Intelligence
        │
        ├──────────────┐
        ▼              ▼
Extractors      Classifier
        │              │
        └──────┬───────┘
               ▼
      Conflict Resolver
               │
               ▼
         Memory Validator
               │
               ▼
        Memory Repository
```

Los componentes nunca deben depender entre sí de forma circular.

---

# 14. Inversión de Dependencias

El Cognitive Engine dependerá únicamente de contratos.

Nunca dependerá de implementaciones concretas.

Ejemplo

Memory Intelligence no debe conocer cómo funciona SemanticExtractor.

Solo debe conocer el contrato MemoryExtractor.

Esto permitirá registrar nuevas implementaciones sin modificar el orquestador.

---

# 15. Evolución

La arquitectura permitirá añadir nuevos componentes como:

- Emotion Analyzer
- Habit Detector
- Preference Learner
- Goal Tracker
- Memory Summarizer
- Knowledge Graph Builder

Todos deberán implementar contratos compatibles.

No será necesario modificar el pipeline.

---

# 16. Filosofía Final

Los contratos representan los acuerdos internos del sistema.

Gracias a ellos, el Cognitive Engine podrá evolucionar durante años manteniendo estabilidad, modularidad y facilidad de mantenimiento.

Las implementaciones podrán cambiar.

Los contratos deberán permanecer estables.
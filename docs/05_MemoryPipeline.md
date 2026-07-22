# Memory Pipeline
## JARVIS-OS
### Documento de Arquitectura

Versión: 1.0  
Sprint: 31

---

# 1. Propósito

El Memory Pipeline define el flujo completo mediante el cual JARVIS transforma una conversación en conocimiento estructurado.

Su responsabilidad es convertir lenguaje natural en memorias consistentes, persistentes y recuperables.

El pipeline es completamente modular.

Cada etapa tiene una única responsabilidad y puede evolucionar independientemente del resto del sistema.

---

# 2. Arquitectura General

```
                 Usuario
                     │
                     ▼
            Text Normalizer
                     │
                     ▼
         Memory Intelligence
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
Rule Extractors              Semantic Extractor
      └──────────────┬──────────────┘
                     ▼
             Memory Classifier
                     │
                     ▼
            Conflict Resolver
                     │
                     ▼
            Memory Validator
                     │
                     ▼
              Memory Ranking
                     │
                     ▼
              LongTermMemory
                     │
                     ▼
            Memory Retriever
                     │
                     ▼
              Context Builder
                     │
                     ▼
                    LLM
```

---

# 3. Etapas del Pipeline

## 3.1 Text Normalizer

Responsabilidad:

Normalizar la entrada del usuario para facilitar el procesamiento posterior.

Funciones:

- eliminar ruido
- normalizar espacios
- eliminar variaciones ortográficas simples
- preservar la intención del mensaje

Salida:

Texto normalizado.

---

## 3.2 Memory Intelligence

Es el orquestador del aprendizaje.

Responsabilidades:

- coordinar extractores
- evitar duplicados
- combinar resultados
- iniciar el proceso de clasificación

No almacena memoria.

No toma decisiones finales.

---

## 3.3 Rule Extractors

Detectan información conocida mediante reglas.

Ejemplos:

- profesión
- proyectos
- idioma
- ubicación
- preferencias conocidas

Ventajas:

- rápidos
- deterministas
- alta precisión

Limitación:

Solo reconocen patrones previamente implementados.

---

## 3.4 Semantic Extractor

Detecta información que no posee un extractor específico.

Ejemplos:

```
Mi color favorito es azul.

Disfruto leer ciencia ficción.

Tengo experiencia en cirugía laparoscópica.
```

Debe producir MemoryFacts compatibles con el resto del sistema.

No reemplaza a los Rule Extractors.

Los complementa.

---

## 3.5 Memory Classifier

Asigna una categoría a cada MemoryFact.

Categorías iniciales:

- Facts
- Preferences
- Goals
- Relationships
- Dynamic State

En el futuro podrán añadirse nuevas categorías sin modificar el pipeline.

---

## 3.6 Conflict Resolver

Analiza posibles contradicciones.

Ejemplo:

Antes

```
Vivo en Tegucigalpa.
```

Después

```
Ahora vivo en San Pedro Sula.
```

Debe decidir si:

- actualizar
- reemplazar
- conservar ambas memorias
- ignorar la nueva información

---

## 3.7 Memory Validator

Verifica que una memoria sea válida antes de persistirla.

Debe comprobar:

- clave válida
- valor válido
- categoría existente
- confianza mínima
- ausencia de duplicados

Las memorias inválidas son descartadas.

---

## 3.8 Memory Ranking

Asigna prioridad a cada memoria.

Factores:

- categoría
- confianza
- recencia
- frecuencia de uso
- relevancia contextual

El ranking permitirá mejorar la recuperación.

---

## 3.9 LongTermMemory

Responsabilidad:

Persistir únicamente memorias aprobadas.

Debe permitir:

- actualización
- eliminación
- búsqueda
- historial

No realiza inferencias.

---

## 3.10 Memory Retriever

Obtiene únicamente las memorias relevantes para la conversación actual.

No devuelve toda la base de conocimiento.

Debe minimizar el contexto enviado al modelo.

---

## 3.11 Context Builder

Construye el contexto final que recibirá el LLM.

Combina:

- memorias recuperadas
- conversación reciente
- instrucciones del sistema
- contexto temporal

El resultado debe ser compacto y coherente.

---

# 4. Flujo Completo

```
Usuario
   │
   ▼
Text Normalizer
   │
   ▼
Memory Intelligence
   │
   ├── Rule Extractors
   ├── Semantic Extractor
   │
   ▼
Memory Classifier
   │
   ▼
Conflict Resolver
   │
   ▼
Memory Validator
   │
   ▼
Memory Ranking
   │
   ▼
LongTermMemory
   │
   ▼
Memory Retriever
   │
   ▼
Context Builder
   │
   ▼
LLM
```

---

# 5. Principios de Diseño

Cada componente debe tener una única responsabilidad.

Los módulos deben estar desacoplados.

Cada etapa debe ser fácilmente reemplazable.

El pipeline debe ser extensible.

Ningún componente debe depender de implementaciones específicas de otro módulo.

La comunicación entre módulos debe realizarse mediante modelos de dominio claramente definidos.

---

# 6. Extensibilidad

La arquitectura permitirá incorporar nuevos módulos sin modificar el resto del pipeline.

Ejemplos:

- Emotional Analyzer
- Preference Learner
- Habit Detector
- Episodic Memory
- Procedural Memory
- Knowledge Graph Builder

Todos deberán integrarse mediante las mismas interfaces del pipeline.

---

# 7. Futuro

Las siguientes capacidades podrán añadirse progresivamente:

- recuperación semántica mediante embeddings
- memoria episódica
- memoria autobiográfica
- memoria procedimental
- razonamiento basado en conocimiento
- detección automática de cambios
- aprendizaje continuo

La arquitectura del pipeline está diseñada para soportar esta evolución sin rediseños mayores.
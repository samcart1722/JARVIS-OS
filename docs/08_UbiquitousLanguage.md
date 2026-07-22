# 08 - Ubiquitous Language

## Introducción

Este documento define el lenguaje oficial del Cognitive Memory Engine.

Todos los componentes de JARVIS deberán utilizar esta terminología.

No se crearán sinónimos para los mismos conceptos.

---

# Memory Fact

Unidad mínima de conocimiento persistente.

Representa un hecho conocido por JARVIS.

Ejemplos:

- El usuario es médico.
- El proyecto principal es HealthBridge.
- El usuario prefiere respuestas completas.

---

# Memory Category

Clasificación de un Memory Fact.

Ejemplos:

- Personal
- Project
- Preference
- Conversation
- Knowledge
- Goal

---

# Memory Source

Origen del conocimiento.

Ejemplos:

- User
- Conversation
- Extractor
- Semantic
- System

---

# Memory Query

Solicitud para recuperar conocimiento.

No contiene memorias.

Solo expresa qué información necesita el sistema.

---

# Memory Result

Resultado de una consulta.

Contiene una o varias memorias ordenadas por relevancia.

---

# Retrieved Memory

Representa una memoria recuperada junto con la información de ranking.

No modifica la memoria original.

---

# Memory Conflict

Describe una contradicción entre dos o más Memory Facts.

Nunca elimina información automáticamente.

Siempre requiere resolución.

---

# Memory Extractor

Componente responsable de transformar conversación en Memory Facts.

---

# Memory Classifier

Componente responsable de asignar categorías.

---

# Memory Validator

Comprueba que una memoria sea válida.

---

# Memory Ranker

Ordena memorias según relevancia.

---

# Memory Repository

Responsable de almacenar y recuperar memorias.

---

# Memory Pipeline

Proceso completo desde la entrada del usuario hasta la persistencia de nuevas memorias.

---

# Cognitive Memory Engine

Conjunto completo de componentes responsables del conocimiento persistente de JARVIS.
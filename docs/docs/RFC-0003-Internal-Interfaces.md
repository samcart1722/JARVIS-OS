# RFC-0003 - Internal Interfaces

Status:
Draft

Author:
OlsanTech

---

# Objetivo

Definir las interfaces públicas entre los módulos principales de JARVIS.

Los módulos nunca deben depender de implementaciones internas de otros módulos.

Toda comunicación se realizará mediante interfaces estables.

---

# Principios

1. Bajo acoplamiento.
2. Alta cohesión.
3. Una responsabilidad por módulo.
4. Interfaces pequeñas.
5. Implementaciones intercambiables.

---

# Memory

Responsabilidad:

Administrar toda la memoria del usuario.

Interfaz pública:

answer(question: str) -> str | None

remember(key: str, value: str)

recall(key: str)

clear_memory()

---

# Knowledge

Responsabilidad:

Administrar el conocimiento aprendido por JARVIS.

Interfaz pública:

answer(question: str)

learn(document)

search(query)

related(concept)

---

# Browser

Responsabilidad:

Obtener información externa.

Interfaz pública:

search(query: str)

---

# Tools

Responsabilidad:

Ejecutar acciones.

Interfaz pública:

execute(command)

---

# Profile

Responsabilidad:

Administrar información permanente del usuario.

Interfaz pública:

answer(question)

update(data)

---

# Model

Responsabilidad:

Generar lenguaje natural.

Interfaz pública:

generate(prompt)

---

# Reasoning

Responsabilidad:

Decidir qué módulo debe responder.

Interfaz pública:

process(user_input)

Nunca accederá directamente a estructuras internas de otros módulos.

Solo utilizará sus interfaces públicas.

---

# Beneficios

- Bajo acoplamiento.
- Fácil mantenimiento.
- Sustitución de implementaciones.
- Mayor capacidad de pruebas.
- Escalabilidad.
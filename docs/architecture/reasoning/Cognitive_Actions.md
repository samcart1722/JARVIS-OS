# Cognitive Actions

Version: 1.0  
Status: Official  
Author: JARVIS-OS Team

---

# 1. Purpose

Cognitive Actions perform the work defined by the Execution Plan.

They are the executable units of the cognitive architecture.

Actions transform an Execution Plan into observable behavior.

---

# 2. Responsibility

A Cognitive Action has one responsibility:

Execute a single cognitive task.

Examples include:

- Retrieving memory.
- Querying knowledge.
- Invoking a language model.
- Calling a tool.
- Producing a response.

A Cognitive Action never:

- Selects strategies.
- Evaluates policies.
- Plans execution.

---

# 3. Position in the Reasoning Flow

```
Execution Plan
      │
      ▼
Cognitive Actions
      │
      ▼
Capability Providers
```

Each action is executed according to the order defined by the Execution Planner.

---

# 4. Characteristics

Every Cognitive Action should be:

- Atomic
- Reusable
- Independent
- Deterministic whenever possible

An action performs one operation and then completes.

---

# 5. Atomicity

A Cognitive Action represents a single unit of work.

Examples:

- RecallMemoryAction
- RetrieveKnowledgeAction
- ReflectAction
- InvokeLLMAction
- ExecuteToolAction
- GenerateResponseAction

Actions should not combine multiple responsibilities.

---

# 6. Independence

Actions must not depend directly on other Actions.

Relationships between Actions are defined by the Execution Plan, not by the Actions themselves.

---

# 7. Capability Delegation

Actions do not implement cognitive capabilities.

Instead, they delegate execution to Capability Providers.

Example:

```
RecallMemoryAction

↓

Memory Provider
```

```
InvokeLLMAction

↓

Language Provider
```

Actions coordinate work.

Providers perform work.

---

# 8. Inputs and Outputs

Each Action receives the information required to perform its task.

Each Action produces an output that becomes available to subsequent Actions in the Execution Plan.

The internal representation of inputs and outputs is implementation-specific.

---

# 9. Architectural Principles

## Single Responsibility

One Action performs one task.

---

## Reusability

The same Action may appear in multiple Execution Plans.

---

## Composability

Actions can be combined into different execution sequences.

---

## Replaceability

An Action may be replaced by another implementation without changing the architecture.

---

# 10. Responsibilities

Cognitive Actions are responsible for:

- Executing work.
- Coordinating capability usage.
- Producing execution results.

They are not responsible for:

- Strategy selection.
- Policy evaluation.
- Planning.
- Decision making.

---

# 11. Relationship with Other Components

```
Execution Planner
        │
        ▼
Execution Plan
        │
        ▼
Cognitive Actions
        │
        ▼
Capability Providers
        │
        ▼
Capabilities
```

Actions form the execution layer of the cognitive architecture.

They translate plans into concrete operations.

---

# 12. Final Statement

Cognitive Actions are the executable building blocks of the reasoning engine.

They execute one cognitive task at a time, following the Execution Plan, while delegating specialized work to Capability Providers.
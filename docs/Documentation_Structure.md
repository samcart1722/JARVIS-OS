# JARVIS-OS Documentation Structure

Version: 2.0
Status: Official
Author: JARVIS-OS Team

---

# 1. Purpose

This document defines the official documentation architecture of JARVIS-OS.

Documentation is considered a first-class architectural asset.

Its purpose is to ensure that every document has a clear responsibility, a defined audience, and a stable location within the project.

The documentation architecture is designed to evolve with the software architecture while preserving consistency, maintainability, and discoverability.

---

# 2. Philosophy

Documentation is not a collection of notes.

Documentation is an architecture.

Like software architecture, documentation should exhibit:

- Clear responsibilities
- Explicit organization
- Stable ownership
- Minimal duplication
- Progressive evolution
- Long-term maintainability

Every document should answer one primary question.

---

# 3. Architectural Principles

The documentation follows the same architectural principles as the source code.

## Single Responsibility

Every document owns one concept.

If a document begins answering unrelated questions, it should be split.

---

## Single Source of Truth

A concept must only be defined once.

Other documents reference the authoritative source rather than duplicating content.

---

## Progressive Disclosure

Documentation progresses from abstract concepts toward implementation.

Readers should never encounter implementation details before understanding the architecture.

---

## Stable Responsibilities

Documents may evolve.

Their responsibilities should not.

Changing the responsibility of a document usually indicates the need for a new document.

---

## Architecture First

Architecture precedes implementation.

Documentation defines the system.

Code implements the documentation.

---

# 4. Documentation Hierarchy

The documentation is organized into architectural layers.

```
Foundation

↓

Architecture

↓

Domains

↓

Implementation
```

Every layer depends only on the layers above it.

Implementation never defines architecture.

Architecture never changes the project's vision.

---

# 5. Documentation Categories

## Foundation

Defines the identity of the project.

Examples:

- FOUNDING.md
- CONSTITUTION.md

These documents rarely change.

---

## Architecture

Defines how the system is designed.

Examples:

- Cognitive Architecture
- Reasoning
- Memory
- Knowledge
- Planning
- Reflection
- Learning
- Infrastructure

Architecture documents describe design.

They do not describe implementation.

---

## Domains

Documents dedicated to individual bounded contexts.

Each domain documents its own architecture independently.

Examples:

- Memory
- Knowledge
- Planning
- Reflection
- Learning

---

## RFC

Request For Comments.

RFCs describe architectural proposals that are still under discussion.

RFCs are exploratory.

They are not architectural truth.

Approved RFCs eventually become architecture.

---

## ADR

Architecture Decision Records.

ADRs permanently record architectural decisions.

Every ADR documents:

- Context
- Decision
- Consequences

ADRs preserve architectural history.

---

## Implementation

Implementation documents describe execution.

Examples:

- Sprint Plans
- Migration Guides
- Checklists
- Rollout Plans

Implementation documents are expected to evolve frequently.

---

# 6. Recommended Directory Structure

```
docs/

│── Documentation_Structure.md

├── foundation/
│     FOUNDING.md
│     CONSTITUTION.md
│
├── architecture/
│
│     Cognitive_Architecture.md
│     Ubiquitous_Language.md
│     Architectural_Invariants.md
│
│     reasoning/
│         Reasoning.md
│         Strategy_Selection.md
│         Strategy_Catalog.md
│         Decision_Policies.md
│         Cognitive_Actions.md
│         Cognitive_Capabilities.md
│         Reasoning_Pipeline.md
│
│     memory/
│         Cognitive_Memory.md
│         Memory_Pipeline.md
│         Memory_Domain.md
│         Component_Contracts.md
│
│     knowledge/
│
│     planning/
│
│     reflection/
│
│     learning/
│
│     infrastructure/
│
├── adr/
│
├── rfc/
│     RFC-0001
│     RFC-0002
│     RFC-0003
│
└── implementation/
      Sprint-XX.md
```

---

# 7. Reading Order

New contributors should read documentation in the following order.

1. FOUNDING

2. CONSTITUTION

3. Documentation Structure

4. Cognitive Architecture

5. Ubiquitous Language

6. Architectural Invariants

7. Domain Architecture

8. RFCs (optional)

9. Implementation Documents

This order progressively introduces the project.

---

# 8. Naming Convention

Document names describe responsibilities.

They do not describe chronology.

Preferred examples:

- Reasoning.md
- Strategy_Selection.md
- Decision_Policies.md
- Memory_Pipeline.md

Avoid names such as:

- Notes.md
- Ideas.md
- Temp.md
- NewVersion.md
- Draft2.md

Document ordering is defined by Documentation_Structure.md rather than filenames.

---

# 9. Document Lifecycle

Every document follows a predictable lifecycle.

```
Idea

↓

RFC

↓

Architecture

↓

Implementation

↓

Maintenance

↓

Historical Reference
```

Not every idea becomes architecture.

Architecture exists only after deliberate approval.

---

# 10. Documentation Dependency Rule

Documentation dependencies always point downward.

```
Foundation

↓

Architecture

↓

Domains

↓

Implementation
```

Rules:

- Foundation never depends on Architecture.
- Architecture may reference Foundation.
- Domains may reference Architecture.
- Implementation may reference every previous layer.
- Circular documentation dependencies are prohibited.

---

# 11. Rules for New Documents

Before creating a new document, ask:

- Does this concept already exist?
- Can an existing document evolve instead?
- Does this deserve its own responsibility?
- Will this still matter in two years?

If the answer is no,

the document probably should not exist.

---

# 12. Responsibilities

Every document answers one primary question.

Examples:

Vision

"What are we building?"

Reasoning

"How does JARVIS think?"

Memory

"How does JARVIS remember?"

Planning

"How does JARVIS plan?"

Decision Policies

"How are reasoning decisions made?"

If a document answers multiple unrelated questions,

it should be divided.

---

# 13. Documentation Quality

High-quality documentation is:

- Precise
- Consistent
- Architecture-oriented
- Implementation-independent
- Maintainable
- Testable by reasoning

Documentation explains decisions,

not code.

---

# 14. Future Evolution

The documentation architecture is expected to grow.

Future categories may include:

- Security
- Deployment
- Observability
- Testing
- Operations
- Research

New categories should extend the documentation hierarchy without modifying existing responsibilities.

---

# 15. Final Statement

Documentation is a first-class architectural asset of JARVIS-OS.

It preserves the project's vision, architectural decisions, and design philosophy.

A well-designed documentation architecture enables long-term evolution without sacrificing clarity, consistency, or maintainability.

Every document should have one responsibility.

Every responsibility should have one document.

The documentation architecture should evolve with the software architecture while remaining simple, coherent, and intentional.
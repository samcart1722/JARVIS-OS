# JARVIS-OS Strategy Catalog
Version: 1.0
Status: Draft
Author: JARVIS-OS Team

---

# 1. Purpose

The Strategy Catalog defines every reasoning strategy available to JARVIS-OS.

Strategies are declarative cognitive configurations.

A strategy describes **what cognitive capabilities are required**, not how they are implemented.

Behavior emerges from the combination of Decision Policies and Cognitive Actions.

---

# 2. Philosophy

Strategies are metadata.

Policies contain rules.

Actions perform work.

The Reasoning Engine orchestrates.

---

# 3. Strategy Model

Every strategy defines:

- Name
- Purpose
- Supported Complexity
- Required Capabilities
- Preferred Policies
- Allowed Actions
- Escalation Rules

Strategies never contain implementation logic.

---

# 4. Capability Model

Capabilities represent cognitive abilities.

Examples:

Memory

Knowledge

Planning

Tools

Reflection

Learning

Context

LLM

Clarification

Capabilities are reusable.

Multiple strategies may share the same capabilities.

---

# 5. Strategy Selection

The Strategy Selector never selects an algorithm.

Instead it searches the catalog for the strategy whose capabilities best satisfy the current objective.

Selection is capability-driven.

---

# 6. Strategy Definition

Every strategy should declare:

Name

Purpose

Capabilities

Complexity

Cost

Confidence

Escalation

No implementation details are stored here.

---

# 7. Example Strategy

Name

Memory First

Purpose

Answer using long-term memory whenever possible.

Capabilities

✓ Memory

✓ Context

✓ Reflection

Complexity

Simple

Cost

Low

Confidence

High

---

# 8. Example Strategy

Name

Research

Purpose

Acquire and synthesize external information.

Capabilities

✓ Knowledge

✓ Planning

✓ Tools

✓ Reflection

✓ Learning

Complexity

Very High

Cost

High

Confidence

Adaptive

---

# 9. Strategy Compatibility

Strategies may require capabilities provided by other domains.

Example:

Research

↓

Knowledge

↓

Planning

↓

Tools

↓

Reflection

Dependencies are declarative.

---

# 10. Strategy Scoring

Multiple strategies may satisfy the same objective.

The selector evaluates:

Capability Coverage

Complexity

Cost

Confidence

Risk

The highest score wins.

---

# 11. Extensibility

New strategies can be introduced without modifying:

Reasoning Engine

Strategy Selector

Decision Policies

Cognitive Actions

Only the catalog changes.

---

# 12. Architectural Rules

Strategies:

✓ declare capabilities

✓ define intent

✓ describe constraints

Strategies never:

✗ execute actions

✗ perform reasoning

✗ access repositories

✗ call tools

✗ invoke LLMs

---

# 13. Future Evolution

Future versions may support:

Dynamic strategy generation

User-specific strategies

Domain-specialized strategies

Autonomous strategy synthesis

without changing public contracts.

---

# 14. Final Statement

The Strategy Catalog defines every cognitive path available to JARVIS-OS.

Strategies are declarative descriptions of cognitive capabilities.

Execution emerges from the orchestration of Decision Policies and Cognitive Actions.
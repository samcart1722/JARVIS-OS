# Project Context

## Identity and purpose

The public/commercial project name is **Luxiom**. Luxiom is a Cognitive
Operating System designed to help people think, decide, and execute through a
stable cognitive core, persistent memory, structured reasoning, and contextual
knowledge. Its platform vision is “one cognitive platform, multiple products,
multiple industries, one core.”

Sources: [`docs/00_Product_North_Star.md`](../00_Product_North_Star.md),
[`docs/foundation/VISION.md`](../foundation/VISION.md), and
[`docs/foundation/COGNITIVE_PHILOSOPHY.md`](../foundation/COGNITIVE_PHILOSOPHY.md).

## Platform model

HealthBridge is the first planned product on Luxiom and is intended to validate
the platform in a real, complex domain. It is a consumer of the Core, not a
special case inside it. Other products should supply domain context without
modifying the Core.

The intended composition is:

- Workspaces supply product/domain context, permissions, entities, and enabled
  capabilities.
- Specialists understand a domain and create plans; they do not execute tools.
- Capabilities are reusable, domain-independent skills.
- Tools and AI models implement capabilities and may be replaced.
- The Core coordinates the lifecycle while remaining independent of any client.

Sources: [`docs/00_Product_North_Star.md`](../00_Product_North_Star.md) and
[`docs/01_Cognitive_Lifecycle.md`](../01_Cognitive_Lifecycle.md).

## Architectural principles

- One domain-independent Core.
- Architecture precedes implementation.
- Capabilities before isolated features; composition before coupling.
- Specialists plan and orchestrate capabilities.
- Capabilities use replaceable tools.
- AI models are reasoning providers, never the Core or owners of memory.
- Decisions should be grounded in evidence and important outcomes explainable.
- Human judgment and authorization remain boundaries for critical actions.
- Simplicity and long-term architectural integrity take priority.

Sources: [`docs/foundation/PRINCIPLES.md`](../foundation/PRINCIPLES.md),
[`docs/foundation/CONSTITUTION.md`](../foundation/CONSTITUTION.md), and the two
primary documents above.

## Cognitive Operating System

“Cognitive Operating System” means intelligence is treated as a continuous,
composed process—perception, memory, understanding, reasoning, planning,
execution, reflection, and learning—not as a chat interface or a single model.
The stable conceptual lifecycle runs from user goal through planning and
capability execution to response and memory update.

This file only summarizes that intent. The authoritative lifecycle is
[`docs/01_Cognitive_Lifecycle.md`](../01_Cognitive_Lifecycle.md); executable
differences are recorded in [Runtime Architecture](03_RUNTIME_ARCHITECTURE.md).

## Limits and non-goals

Luxiom is not a chatbot, an LLM wrapper, a conventional agent, a tool
collection, or an industry-specific product. It must not replace professional
human judgment, autonomously make critical decisions, mutate sensitive
information without authorization, learn indiscriminately from every user, or
depend on one AI provider.

## Evolution strategy

Add products through Workspaces, domains through Specialists, skills through
Capabilities, and technology through Tools. Keep the Core stable and record
material architectural decisions. The repository currently contains historical
JARVIS-OS identity and legacy modules; continuity work records this mismatch
without performing rebranding.

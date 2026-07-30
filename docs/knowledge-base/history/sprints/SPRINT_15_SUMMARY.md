# Sprint 15 Summary — Functional Cognitive Demo v1

Added a local CLI comparison between baseline reasoning and memory-aware
reasoning. It requires an explicit prompt, memory scope, and one or more
synthetic records. Records live only in a dedicated in-memory repository for
the command.

The demo copies the same provider configuration and prompt limits into two
independent containers. Reasoning is enabled in both. Retrieval and prompt
memory are disabled for baseline and enabled for the scoped comparison. The
base Settings object and process environment are not mutated.

`FunctionalCognitiveDemoRuntime` validates input, checks readiness exactly
once, and runs neither engine when readiness fails. When ready, it executes
baseline once and memory-aware reasoning once. Both visible outcomes preserve
existing structured failures; there is no retry or fallback.

`CognitiveDemoComparison` is immutable. It carries safe canonical readiness, a
positive ephemeral-record count, an explicit-scope boolean, and both optional
cognitive outcomes. Failed readiness requires absent outcomes; ready readiness
requires both outcomes. It stores no scope, identifier, URL, prompt,
exception, or infrastructure object.

Synthetic record content includes the demo query because the scoped repository
uses literal query matching. This enables controlled retrieval without
changing persistence semantics. Prompt policy still labels retrieved content
as bounded, untrusted reference data. Its stable wrapper preserves the user
payload, adds no hidden facts, and never serializes the scope.

Tests use mocks instead of Ollama or network access. They verify call counts,
readiness failures, structured outcomes, Settings isolation, ephemeral
composition, identical provider/model configuration, unchanged baseline
prompt, and memory-only prompt context. The public API remains unchanged.

The runbook records prerequisites, exact usage, safe failures, exit codes,
command-history risk, ephemeral behavior, and current limitations.

Real technical debt remains the global legacy repository, legacy records
without ownership, and the historically imprecise `OLLAMA_BASE_URL` name.

Deliberately deferred roadmap includes durable persistence, writes, Memory
Update, legacy migration, authentication and identity, HTTP scope integration,
UI and installable distribution, advanced prompt-injection defense, ranking,
token limits, retention, and deletion. Governance maintenance must keep the
explicit AST file lists synchronized as the demo surface grows.

Demo limitations are literal retrieval, a query-addressable wrapper intended
only for synthetic demo data, generative-provider variability, and no durable
memory.

Final validation with `DEBUG=true`: **221 passed, 1 pre-existing pytest cache
warning**. Ruff and `git diff --check` passed. Isolated demo/runtime/Container
tests passed 46; API and architecture passed 29; reasoning, readiness, memory,
and prompt tests passed 66.

The prescribed real local execution was attempted once because Ollama was
available. Readiness was `ready`, both cognitive paths executed successfully,
and the command exited 0. Baseline reported insufficient Luxiom knowledge;
memory-aware output used the synthetic scoped references and mentioned
HealthBridge. These generated answers are execution evidence, not factual or
quality guarantees.

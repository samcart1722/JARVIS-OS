# Sprint 14 Summary — Memory-Aware Reasoning Prompt Policy v1

Added `ReasoningPromptBuilder`, an exact normalized-input compatibility
builder, and `MemoryAwareReasoningPromptBuilder`. Prompt memory is independently
disabled by default. Missing and empty snapshots preserve the historical
prompt exactly.

Enabled non-empty memory produces stable current-request, untrusted-reference,
and response-instruction sections. Records are JSON strings so stored line
breaks and quotes remain data. Safety text prohibits following stored
instructions, prioritizes current request/system rules, and permits ignoring
irrelevant or conflicting records. This is a basic control, not complete
prompt-injection prevention.

Only the first configured records participate. Their combined source content
is truncated sequentially to a positive character budget; the request is
never truncated. Ordering and Unicode are preserved and scope identifiers are
not serialized.

Settings default to disabled, five records, and 2,000 memory characters.
Container injects the builder into OllamaProvider. The provider builds once,
sends exactly that string to the client, and never retrieves memory.

Controlled tests cover all combinations, limits, malicious instruction-like
data, cross-scope exclusion, provider delegation, Settings, composition, and
architecture without network or external I/O.

API and demo remain unchanged. No write, Memory Update, legacy access,
migration, fallback, retry, embedding, ranking, tokenizer, or dependency was
added.

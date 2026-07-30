# Sprint 17 Summary — Evidence-Bounded Memory Reasoning v1

Sprint 17 adds an opt-in, evidence-bounded reasoning protocol for non-empty
scoped memory snapshots. The historical memory-aware path remains exact when
the independent flag is false, or when no usable snapshot exists.

`MemoryEvidenceSelector` deterministically selects and numbers records using
the existing record-count and character budgets. The grounded prompt builder
and provider decorator share that policy, so validation uses the exact visible
record range without hidden state.

`JsonGroundedResponseParser` accepts one strict JSON object containing exactly
`status`, `answer`, and `used_record_numbers`. It rejects malformed or
decorated output, invalid types and statuses, duplicate or out-of-range
references, and invalid status invariants. It performs no repair, substring
extraction, I/O, retry, or fallback and never stores the raw response in its
safe protocol error.

`EvidenceBoundedReasoningProvider` calls its injected provider exactly once.
It passes historical results through unchanged when grounding does not apply
and preserves inner failures without parsing. A valid `answered` envelope
renders the answer plus stable record-number evidence; an
`insufficient_evidence` envelope renders a deterministic safe message.
Invalid protocol becomes the controlled cognitive code
`grounded_response_protocol_invalid`, without exposing raw model output,
scope, or record contents.

Container remains the composition root. Grounding defaults off through
`MEMORY_GROUNDED_RESPONSE_ENABLED=false`; construction performs no retrieval,
parsing, reasoning, readiness check, network call, or persistence. Ollama
remains transport-only and the public API gains no endpoint or scope surface.

The local comparative runtime performs one readiness check, one standard
memory-aware execution, and one grounded execution with the exact same prompt,
scope, and synthetic records. Its immutable report stores safe readiness,
outcomes, count, and an explicit-scope boolean, but not the scope, prompt,
records, provider response, or infrastructure.

The protocol improves structural discipline and auditability. It does not
verify truth, semantically prove claims against records, eliminate
hallucinations, or provide complete prompt-injection defense. Fact checking,
second-model evaluation, web or external retrieval, embeddings, persistence,
identity, automatic memory extraction, retries, JSON repair, and free-text
fallback remain outside scope.

Final validation with `DEBUG=true`: **329 passed, 1 pre-existing pytest cache
warning**. Ruff and `git diff --check` passed.

Ollama was available. The prescribed effective execution ran once after
supplying the required valid local `DEBUG=true`: readiness was `ready`; both
standard and grounded paths succeeded; exit code was 0. The grounded response
used records 1 and 2 and included the stable evidence footer. Its wording
still contained interpretation beyond literal record text, illustrating the
documented limit: a valid envelope and valid references improve auditability
but do not prove semantic support or truth.

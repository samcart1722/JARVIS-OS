# Sprint 19 Summary — Model-Assisted Claim Evidence Support Verification v1

Sprint 19 adds a disabled-by-default support gate after strict Sprint 18 claim
parsing. One generator call is followed by at most one verifier call containing
only claims and cited bounded evidence. Strict verdict parsing and an
all-or-nothing decision preserve Sprint 18 formatting only when all claims are
supported. Invalid verifier protocol uses a safe controlled 503 error.

The inherited Sprint 18 flow calls the same deterministic
`MemoryEvidenceSelector` instance from the prompt builder and provider against
the same immutable snapshot. Selection is therefore recomputed; memory is not
retrieved again and the repository is not accessed again.

Historical, Sprint 17, and Sprint 18 routes remain exact unless all three flags
are enabled. This does not solve truth, independent verification, deterministic
entailment, contradictions, atomicity, confidence, partial filtering, human
review, durable audit, HTTP exposure, or external verification. The same model
can falsely support or reject claims. Inherited global-memory, ownership, and
historical URL-naming debt remains.

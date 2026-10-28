# Sprint 42 — Behavior Contract Amendment 01 — Positive Eligibility and Semantic Role Validation

Status: FROZEN AMENDMENT — PENDING INDEPENDENT REVIEW — NOT YET EFFECTIVE

Date: 2026-10-28, America/Tegucigalpa.
Scope: Sprint 42 — Governed Local Model-Assisted Intent Preparation v1.
Authority: SPRINT_42_CONTRACT_CLARIFICATION_AUTHORIZED, documentation only.

## 1. Immutable original and effectivity

Original frozen contract:
`docs/knowledge-base/SPRINT_42_GOVERNED_LOCAL_MODEL_ASSISTED_INTENT_PREPARATION_CONTRACT.md`.
Original Git blob: `37e2e5880cb4f93594e5ad31501c6213566be1be`.
Canonical SHA-256 of exact raw Git blob bytes:
`338A81AA5C8B225207A771E7C1E3D9A477DBC71190860BE16E7FA47AFA395B06`.
The original remains immutable: no replacement, rewrite or checkout normalization.

This amendment is additive/superseding ONLY for the identified eligibility,
semantic-role and gate-composition clauses below. Every other original provision
remains authoritative. It becomes effective ONLY after independent amendment
review approval AND governed merge. Freezing this candidate on its documentation
branch does not make it effective or authorize implementation.

Block A2 and Block B are NOT AUTHORIZED. Block B remains prohibited until this
amendment is effective and a separately authorized Block A2 implements/tests this
clarification and receives independent review approval. Neither this document nor
its future merge substitutes for explicit implementation authorization.

## 2. Precisely identified overlay

| Original clause | Limited amendment |
|---|---|
| Section 3, otherwise-safe unrecognized eligibility and unknown/uncertain default | Sections 4-6 below define a positive guard-complement decision, not intent recognition |
| Section 4, unknown/uncertain safety/structural framing | Frozen guards/precedence retained; semantic non-recognition alone is not a safety failure |
| Section 8, independent semantic role proof for CAPTURE/RECALL | Sections 9-10 below define schema, grounding and absence-of-authority proof; provider proposes semantics |
| Section 8, ADD/READ roles | Section 11 retains strict structural destination evidence and pre-destination item grounding |
| Sections 9, 10, 14-17, relationship of eligibility, validation, proposal and execution | Sections 12-15 clarify composition only; existing command/transport/authority rules do not change |
| Sections 18-19, required tests and block sequencing | Section 17 adds separately authorized A2 alignment before Block B; existing regression/authority gates remain |

No other clause is superseded. In a conflict limited to the overlay above, this
amendment governs only AFTER effectivity; until then the original contract and
existing safe fail-closed implementation remain unchanged.

## 3. Reason and independent-review finding

Block A independent review found assess_eligibility() deliberately fail-closed:
no positive eligible_unrecognized result is produced. The approved contract supplied
no deterministic positive paraphrase vocabulary. Inventing synonyms, scoring or
heuristics would violate that freeze. Therefore a future provider cannot be invoked
through the current eligibility implementation. This was safe and contract-faithful
under the prior ambiguous wording, rather than authorization to invent a corpus.

The original sentence, "Deterministic role validation MUST confirm that slices
represent the specified semantic fields", also needs a precise CAPTURE/RECALL
meaning. Independent natural-language semantic proof would require inventing a
second language recognizer or relying on the model's semantic proposal. The latter
is now explicitly distinguished from deterministic schema/grounding/authority proof;
no duplicate semantic interpreter is required.

## 4. Normative eligible_unrecognized meaning

eligible_unrecognized means: **The text is valid/bounded, is not handled by the
frozen Sprint 41 deterministic preparation corpus, and every explicitly frozen
protected/safety guard has deterministically passed.**

It does NOT mean the text is known to express a supported intent, that the provider
will return supported, that a command exists, that the request is authorized or
that an action may execute. It permits ONLY one bounded local-model classification/
extraction attempt when session-level local-model assistance opt-in is ON.
The provider may return supported OR unsupported. Eligibility is permission to ASK
the bounded local model, not a positive semantic classification.

## 5. Exact deterministic decision rule and precedence

Apply existing frozen deterministic gates in their frozen precedence. Return
protected when ANY of the following applies:

- Invalid/non-string input, empty/frozen-whitespace-only input, more than 8192
  Unicode code points in original input, or isolated surrogate.
- Frozen Sprint 41 deterministic intent/Prepared recognition OR recognizable
  ClarificationRequired, including missing/invalid explicit-field cases.
- Leading bounded top-level no, si or cuando; standalone frozen si/cuando guard.
- Whole-request ASCII/curly quotation framing or Por ejemplo: framing.
- Frozen multiple-action detector or frozen context-reference words.
- Ambiguous destination structure, direct bounded knowledge namespace or direct
  bounded list namespace (including malformed commands).
- Any other deterministic condition classified as protected by the existing frozen
  Sprint 41 safety precedence; unresolved safety/structural evidence stays protected.

Do not reorder or weaken invalid-input, condition, framing, multi-action, context,
destination, recognition or direct-command protections. Original contract section 4
and Sprint 41 sections 5-7 continue to define keyword mapping, exact outer whitespace,
question wrappers, standalone boundaries, destination ambiguity, multi-action
boundaries/introducers and quoted-span suppression. No new synonyms, broad negation
vocabulary, scoring, fuzzy classifier, embeddings or language-model eligibility
calls are introduced. Direct namespace protection remains whitespace/end bounded.
A prior unsupported_request reason alone still cannot authorize model use.

Only when ALL three conditions hold:

1. Original input is valid/bounded.
2. No deterministic Sprint 41 intent/clarification matched.
3. Every frozen protected guard is false.

return EligibilityDecision.ELIGIBLE_UNRECOGNIZED with stable reason safe_unrecognized.
No positive synonym list or new deterministic intent corpus is required. Browser
and server must independently apply the same effective frozen semantics; a browser
eligible=true flag or a caller-supplied reason is never trusted.

## 6. Unknown/uncertain safety versus semantic non-recognition

The original phrase "Unknown/uncertain cases are protected" now means:
**Unknown/uncertain SAFETY OR STRUCTURAL cases remain protected.**
Mere semantic non-recognition is NOT itself a safety ambiguity. A bounded request
whose intent is unknown to the deterministic Sprint 41 recognizer, but whose safety/
structure passes every frozen protected guard, is eligible_unrecognized. It remains
semantically unknown until the local model returns a closed candidate or unsupported.
Do not create a second lexical intent recognizer to decide whether to ask the model;
do not use this clarification to bypass any frozen safety guard.

## 7. Deterministic first and consent remain absolute

| Input/consent state | Model calls |
|---|---|
| Sprint 41 Prepared recognition | ZERO |
| Sprint 41 ClarificationRequired recognition | ZERO |
| Protected/safety Unsupported | ZERO |
| Direct local command namespace | ZERO |
| Session opt-in OFF | ZERO |
| eligible_unrecognized AND session opt-in ON | At most ONE per explicit Interpret attempt |

No retry, repair call, automatic second call, external fallback or background
generation. Session consent remains default OFF, nonpersistent and cleared on
refresh/restart. It permits interpretation assistance only, never execution.

## 8. Eligibility examples — not a new recognition corpus

Assuming no other protected condition, the following illustrate the generic rule:

| Original text | Eligibility |
|---|---|
| Conserva café molido | eligible_unrecognized / safe_unrecognized |
| Busca Tema Ágil | eligible_unrecognized / safe_unrecognized |
| Incorpora pan a la lista Compras | eligible_unrecognized / safe_unrecognized |
| Consulta la lista Compras | eligible_unrecognized / safe_unrecognized |
| Hola | eligible_unrecognized / safe_unrecognized |

These are testing examples, NOT deterministic recognition templates and MUST NOT
be added to the Sprint 41 recognizer. Hola is intentional: eligibility permits only
bounded local classification. A compliant provider should normally return unsupported
when text does not map to one of the four intents; eligibility never guarantees it.

Protected examples remain protected: No conserves café; Cuando consulta la lista
Compras; whole quoted/example requests; frozen multi-action/context-reference
requests; direct knowledge ... or list ...; and recognized deterministic Sprint 41
requests such as Recuerda que X, Qué sabes de K or Agrega X a la lista L.

## 9. Clarified model-assisted CAPTURE semantics

For CAPTURE_KNOWLEDGE the provider proposes the semantic intent and field role.
The deterministic validator does NOT implement a second natural-language semantic
parser. The model-assisted acceptance path MUST deterministically enforce:

- Original request was eligible_unrecognized, correlated to the exact same original
  text as the provider request and candidate validation (section 12).
- Intent is exactly CAPTURE_KNOWLEDGE; ONLY value is provider-extractable.
- value is nonempty after the original frozen edge trimming, within frozen field/
  input/surrogate limits and an exact literal contiguous substring of ORIGINAL input.
- Case, accents, Unicode/combining characters and interior whitespace are preserved;
  no translation, summary, synonym substitution or normalization to another string.
- No command, authority or operational metadata fields and no hidden defaults.

The provider MUST NOT create record_id, kind, key, source_type, source_reference,
workspace, actor, permission or proof. Capture operational metadata remains explicit
deterministic user controls; identity/workspace/permission/proof remain their existing
governed boundaries, never model-candidate fields. Missing operational Capture
metadata still yields later deterministic clarification. No generated ID/provenance.

The deterministic proof is **closed schema + literal grounding + absence of
authority**, not independent full Spanish semantic interpretation. Existing inert
literal payload/escaping rules remain unchanged; model output never supplies a final
command. A semantically wrong but schema-grounded proposal is possible and remains
subject to visible review and existing downstream authority.

## 10. Clarified model-assisted RECALL semantics

For RECALL_KNOWLEDGE the provider proposes intent and the semantic role of key.
The model-assisted acceptance path MUST enforce eligible_unrecognized for the exact
same original input, exact RECALL_KNOWLEDGE intent, ONLY key extractability, nonempty
bounded value, exact literal contiguous grounding and case/Unicode/interior-whitespace
preservation. No hidden kind, semantic/vector retrieval, synonym expansion, record
selection, generated query text or command authority.

The validator need NOT independently linguistically prove that the literal substring
is "really" the topic. This semantic proposal comes from the bounded model and remains
subject to visible user review. Optional kind remains an explicit control under the
original contract. Execution is existing exact-key FIND only after explicit Send;
no automatic READ or semantic answer synthesis is introduced.

## 11. ADD/READ structural role evidence remains stricter

Do NOT relax original explicit destination evidence:

- ADD_FOLLOW_UP allows provider item/list_id, but requires one unambiguous terminal
  ` a la lista <list_id>` construction in ORIGINAL input. item must be grounded in
  the pre-destination portion, not merely in the destination itself.
- READ_FOLLOW_UP allows provider list_id, requiring one unambiguous terminal
  `la lista <list_id>` construction, subject to the existing permitted question wrapper.

Retain original keyword comparison, fixed separators, exact identifier matching,
quote/structural evidence and ambiguity restrictions. No hidden/default list, mis
pendientes default, mis tareas default, esa lista resolution, bare la lista default,
multi-token/whitespace ID, :: list ID, | item or silent multi-item splitting. Multiple
destination constructions remain ambiguous/rejected. A coincidental ID elsewhere
is insufficient. The model may broaden surrounding verbs/wording, never invent or
resolve the destination. Explicit controls cannot substitute for required original-
text destination evidence on the model-assisted path.

## 12. Eligibility and candidate validation are separate gates

Successful semantic validation by itself authorizes neither provider usage nor
model-assisted preparation. Future orchestration MUST require BOTH:

1. EligibilityDecision.ELIGIBLE_UNRECOGNIZED for the ORIGINAL input.
2. Accepted candidate validation against that EXACT SAME original input.

A directly supplied Candidate cannot bypass eligibility. Do not treat a caller's
eligibility assertion as evidence; calculate it from text at the owning boundary.
The provider request, candidate validation and proposal correlation must refer to
the same original text, without substituting a new or normalized input.

The validator may remain independently testable. Its complete status means ONLY
complete semantic candidate: never eligible, authorized, executable or trusted.
Capture semantic completeness still omits required operational metadata. Partial
semantic data still needs deterministic clarification/completion and grants no
command authority. These isolated results cannot bypass orchestration's first gate.

## 13. User review and execution authority

The model may semantically misclassify otherwise-safe unrecognized text. Such errors
MUST remain non-authoritative. A valid candidate produces at most deterministic
visible/editable proposal data. The user may inspect, edit or reject; explicit Send
is the ONLY execution boundary and sends the exact visible editor text.
Existing authentication, principal mapping, workspace, membership, permission,
interpreter and gateway remain authoritative. A model error cannot bypass them.
No new automatic command construction authority, Send, permission or execution path.

## 14. Closed provider unsupported result

For ANY eligible input the provider may return exactly:

`{"outcome":"unsupported","intent":null,"fields":{}}`

No command, retry, second provider, cognitive fallback or external model follows.
This does not alter eligibility. Original strict JSON, size, failure containment,
local-only policy and one-call rules still apply.

## 15. Future endpoint consequence (no endpoint authorized here)

Future Block B POST /local/intent-preparation independently calculates eligibility
from text. Browser sends no eligibility flag. Protected/recognized input causes
ZERO provider calls. eligible_unrecognized may cause one preparation-service call.
Session opt-in is the UI-side decision whether the browser calls the endpoint;
direct endpoint access still cannot bypass server eligibility. All original
loopback, Host/Origin/JSON/CSRF and non-executing text-only request protections remain.
No endpoint, provider adapter or network integration is created by this amendment.

## 16. Block A implementation/review truth and preservation

Block A was explicitly user-authorized: SPRINT_42_BLOCK_A_IMPLEMENTATION_AUTHORIZED.
Independent review verdict: SPRINT_42_BLOCK_A_APPROVED_FAIL_CLOSED.
Implementation branch:
`feat/sprint-42-governed-local-model-assisted-intent-preparation`.
Commit: `b3aa7a31faa681e0ec9694781b385a08008b8c35`.
Parent: `cfa15be46d860747ae066f0cafc1a6c5151081e8`.
Exact scope: 13 new files under app/cognition/intent_preparation/ and
tests/unit/cognition/intent_preparation/ (seven production, six test files).

Block A is NOT merged; no implementation PR exists. Its conservative
assess_eligibility() produces no positive eligible case. Review judged this safe and
contract-faithful under the prior ambiguity; Amendment 01 is required before enabling
the positive path. Its original commit/branch MUST remain intact in this gate:
no amendment, extra implementation commit, rebase, master merge, deletion or force push.

Implementation-gate local evidence reported by Codex: 574 Block A tests PASS,
246 existing interpretation tests PASS and Ruff PASS. These are reported historical
local implementation evidence, NOT fresh independent or remote test executions.
No pytest/Ruff/model execution occurs in this documentation gate.

## 17. Required later Block A2 — Positive Eligibility Alignment

AFTER independent amendment approval and governed merge, a small separately
authorized Block A2 is required. Expected future scope:

- Bring the implementation branch forward from updated master WITHOUT rebase or
  history rewriting, preserving Block A commit lineage.
- Implement safe_unrecognized -> ELIGIBLE_UNRECOGNIZED and positive-rule examples.
- Prove all recognized/protected cases still yield PROTECTED in frozen precedence.
- Test that candidate validation cannot substitute for original-input eligibility.
- Preserve CAPTURE/RECALL literal-grounding semantics and ADD/READ strict evidence.
- Run Block A and interpretation regressions, remaining provider/network/model independent.

Block A2 is NOT AUTHORIZED by this amendment prompt/document. Block B remains NOT
AUTHORIZED until effective amendment, separately authorized A2 alignment and its
independent review approval. Subsequent block work still needs explicit authorization.
No Block B/C/D/E implementation is authorized or advanced by this gate.

## 18. Original areas expressly unchanged

No change to four intents; session default-OFF opt-in; closed model-output JSON;
32768-byte provider response bound; 30-second maximum timeout; one-call/no-retry;
loopback-only policy; Host/Origin/CSRF; requests>=2.32,<3 future dependency decision;
no automatic model pull/install/substitution; provider/model agnosticism; explicit
Send; four-field execution envelope; REASONING_ENABLED=False; foreign custody;
Block B/C/D/E boundaries; original non-goals and existing command grammar.
No source/test/dependency/config changes in this gate. No Git EOL configuration or
attributes changes. Canonical hashes use exact Git blob bytes, not checkout CRLF.

## 19. Foreign custody and documentation gate

Foreign tree tests/unit/reasoning/ remains E. INSUFFICIENT_EVIDENCE, untracked,
unstaged, unmodified, outside scope. Known-file SHA-256:
`45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C`.
Only status/hash verification permitted; no content read, import, execution,
collection, lint, staging, moving, renaming, modification, deletion or copying.

Allowed change set is exactly this new amendment, LUXIOM_CANONICAL_PROJECT_STATE.md
and docs/knowledge-base/02_CURRENT_STATE.md. Preserve Sprint 40/41 historical truth
and immutable tags; do not modify original contract or Block A's 13 files.
After finalizing, record amendment Git blob and raw-byte canonical SHA-256 in both
state documents and PR body; any later amendment change requires recomputing all
references before commit. No self-hash is embedded in this amendment.

Next gate: INDEPENDENT AMENDMENT 01 REVIEW. After documentation commit, normal push
and amendment PR: HARD STOP. Do not merge the PR, modify Block A, implement A2/B,
create endpoint, edit pyproject.toml or install/download/generate any model.

AMENDMENT 01 IS NOT YET EFFECTIVE. BLOCK A2 AND BLOCK B ARE NOT AUTHORIZED.

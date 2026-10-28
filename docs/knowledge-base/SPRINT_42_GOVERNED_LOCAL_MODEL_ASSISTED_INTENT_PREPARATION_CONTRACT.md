# Sprint 42 — Governed Local Model-Assisted Intent Preparation v1 — Frozen Behavior Contract

Status: FROZEN BEHAVIOR CONTRACT — IMPLEMENTATION NOT YET AUTHORIZED

Date: 2026-10-28, America/Tegucigalpa. Frozen on
`docs/sprint-42-behavior-contract` for independent contract review; this does NOT
claim that this contract PR has been independently approved or merged.
Implementation requires separate explicit user authorization AFTER independent
review of this PR. No block is authorized merely by freezing this contract.

## 1. Authority, baseline and immutable history

Planning verdict: SPRINT_42_PLANNING_BASELINE_APPROVED. Planning PR #78 merged
normally at `cdce8a09273b209dc310f442f19fe87ec998d119`, ordered parents:
`42e66d67248dd11ffceaad534f2462fb85e25d53` and
`f89384cbf20e4f0ac52670a5c0c16d74fcd39909`; merged tree:
`32e895959d4e35a0dc92b31586e422685774f824`.
Planning commits `919619172bb28d85808ccc2e198c290230d13344` and
`f89384cbf20e4f0ac52670a5c0c16d74fcd39909` are preserved without amendment.
This contract branch starts at that exact merged master.

Sprint 41 remains FORMALLY CLOSED; its frozen behavior and execution grammar
remain authoritative except for the explicitly added opt-in preparation path here.
Sprint 40 guided behavior remains preserved. Neither immutable release tag moves:

| Tag | Object | Peel |
|---|---|---|
| governed-sprint-40-complete | 22044ff154287c000251a16e503807151104e81f | 3a3b607d94e359a1410f29da894882424fadb6f6 |
| governed-sprint-41-complete | 7a9f9e91e62b2b2618f3b68a9107fc1b2d0f66b3 | de191a93c710e50509a738747490a38530f6d43a |

Sprint 41 release tree remains `cc2c2c1637a71d9f949e08eb84e9eb767b917730`.
Baseline document: SPRINT_42_GOVERNED_LOCAL_MODEL_ASSISTED_INTENT_PREPARATION_PLAN.md.
Its corrected Section D supersedes the original foreign-provenance assertion.

## 2. Core product invariant and flow

Broaden Spanish natural-language preparation using EXACTLY these four families:
CAPTURE_KNOWLEDGE, RECALL_KNOWLEDGE, ADD_FOLLOW_UP, READ_FOLLOW_UP.
No fifth intent, new execution capability or model authority.

User text -> deterministic Sprint 41 preparation/safety path -> optional local
assistance ONLY for an eligible unrecognized paraphrase -> closed candidate ->
deterministic validation -> deterministic source grounding -> existing deterministic
command construction -> visible/editable editor -> explicit Send -> existing
authenticated governed execution path.

The model does not execute, authorize, Send, choose actor/workspace/permissions,
read repositories/memory or produce executable command authority.

## 3. Deterministic first and dedicated eligibility

Prepared, ClarificationRequired and protected/safety Unsupported MUST cause ZERO
model calls. Already recognized deterministic intent/clarification never goes to
a model, even with opt-in ON. Only a genuine otherwise-safe unrecognized paraphrase
may be eligible. At most ONE local-model request per explicit eligible Interpret
attempt; no automatic second call, retry, repair loop, cloud/external fallback or
background generation.

Sprint 41's unsupported_request is overloaded: it includes both unrecognized
phrases and protected negated/quoted/example/conditional framing. A reason string
alone MUST NOT authorize model use. Introduce a dedicated deterministic eligibility
decision distinct from that reason: eligible_unrecognized or protected. Unknown/
uncertain cases are protected. Server and browser independently apply the SAME
frozen semantics; never trust browser eligible=true or a caller reason flag.
The text-only endpoint supplies no eligibility flag.

## 4. Protected inputs and safety semantics

Model requests are forbidden for:

- Non-string/invalid, empty/whitespace-only, more than 8192 Unicode code points,
  or isolated-surrogate input.
- Top-level negation; bounded leading si or cuando conditional framing.
- Whole-request quotation/example framing; multiple actions; ambiguous destination.
- Context-reference pronouns covered by Sprint 41; deterministic recognition or
  clarification; direct local command namespace instead of natural language.

Apply existing Python-compatible edge whitespace for inspection and extraction:
U+0009-U+000D, U+001C-U+0020, U+0085, U+00A0, U+1680, U+2000-U+200A,
U+2028-U+2029, U+202F, U+205F, U+3000. Count Unicode code points, not UTF-16 units.
For keyword comparison only map ASCII A-Z and ÁÉÍÓÚÜÑ to lowercase as Sprint 41;
no locale folding, accent removal or normalization of user data. Standalone words
have boundaries at input edges or non-Unicode-letter/non-Unicode-number characters.

Preserve Sprint 41 contract sections 5-7 recognition, safety precedence, exact
multi-action detector and explicit-field conflicts. In particular the multi-action
boundaries remain y, y también, luego, después, entonces with their displayed
ASCII spaces; semicolon/period/exclamation/question followed by ASCII space; and
LF/CRLF/CR with optional ASCII indentation. Introducers remain recuerda, guarda,
anota, agrega, añade, agrégalo, añádelo, muéstrame, optional ¿ plus qué, followed
by ASCII space. Balanced non-nested ASCII/curly double quoted spans suppress that
detector only; odd-backslash ASCII quote escapes and unmatched-quote handling
remain exactly Sprint 41. Never reinterpret quoted contents as instructions.

Leading bounded no/si/cuando, opening ASCII/curly double quote or por ejemplo:
framing cannot be reclassified as eligible. Existing standalone context words
esto, eso, aquello, ello, él, ella, ellos, ellas remain protected. Existing matching
requests containing standalone si/cuando remain conditional. For unrecognized
paraphrases, conservatively protect standalone si/cuando too; no condition or
schedule is inferred. Direct knowledge/list namespace at input start followed by
whitespace or end is protected regardless of command validity; do not feed malformed
commands to the model for repair. Additional apparent negation, quotation/example,
multiple-action or unclear framing is uncertain/protected, not license to infer a
safe positive action. No claim of unrestricted language/safety understanding.

Neither validation nor local model may turn a rejected request into its opposite.
Recognized negative statements inside valid Capture payload remain literal data
under the existing deterministic path; do not silently broaden that path.

## 5. Session consent

UI label: Allow local model assistance. Session-only, default OFF, not persisted,
cleared on refresh/restart. OFF preserves ordinary deterministic Sprint 41 behavior;
eligible unrecognized text remains non-model-assisted. ON still runs deterministic
processing first and contacts a local model only if eligible. The toggle permits
local interpretation assistance only, never execution authority. No localStorage,
sessionStorage, database, history or persistent prompt/response state.

## 6. Specialized core provider contract

Use an architecture-owned specialized contract equivalent to IntentPreparationProvider.
It consumes bounded textual input and returns only a closed semantic candidate/result
or bounded failure. Do NOT reuse ReasoningProvider.generate(CognitiveContext).
No dependency on CognitiveEngine, memory retrieval, repositories, gateway, actor,
workspace, permissions, membership, execution proof or planning engine. This is a
LUXIOM core capability, with HTTP/Ollama behind adapters, not a UI/Ollama helper.
Provider/model identifiers do not enter domain intent contracts.

## 7. Exact model-output contract

Exactly one bounded JSON object with EXACTLY outcome, intent, fields:

| outcome | intent | fields |
|---|---|---|
| supported | Exactly one of the four allowed intent strings | Object with only allowed semantic string fields below |
| unsupported | null | Empty object |

| Supported intent | Only allowed field names |
|---|---|
| CAPTURE_KNOWLEDGE | value |
| RECALL_KNOWLEDGE | key |
| ADD_FOLLOW_UP | item, list_id |
| READ_FOLLOW_UP | list_id |

Partial allowed field sets may yield clarification, never a command with missing
required fields. Present fields must be strings nonempty after permitted edge
trimming; no arrays, nested field structures, type coercion or null field values.
Reject unknown/duplicate JSON keys at ANY object level, fifth/unknown intents,
tool names, command fields/text, multiple candidates, alternatives, markdown fences,
leading/trailing prose or trailing JSON/data. Only JSON framing whitespace may
surround the single object; it must not conceal prose or a second value.
Provider schema/prompt enforcement is advisory; deterministic parser/validator is
authoritative. Do not eval/execute/import model output.

Command text returned instead of the closed candidate is rejected. Literal command-
like text inside a valid source-grounded semantic payload remains inert data under
existing escaping/grammar checks, never a second executable operation.

## 8. Literal source grounding and role validation

Every extracted string MUST be a literal contiguous substring of the ORIGINAL
request, permitting ONLY the edge trimming set in section 4. After trimming, exact
string comparison must find that contiguous original slice. Preserve case, accents,
Unicode/combining characters and interior whitespace. No translation, summary,
semantic rewriting, normalization to another string or invented operational data.
Each extracted field is bounded by the 8192-code-point input bound and independently
rejects isolated surrogates. Grounding precedes acceptance/serialization.

Literal presence is necessary, not sufficient. Deterministic role validation MUST
confirm that slices represent the specified semantic fields; a coincidental word
elsewhere is not operational evidence. Insufficient evidence yields clarification
or Unsupported with no command, never a guessed role. Prompt instructions in user
text or model output grant no validator or execution authority.

CAPTURE: only value may be extracted. NEVER invent record_id, kind, key,
source_type or source_reference. Existing explicit controls supply required metadata;
missing/invalid/conflicting metadata remains clarification. No hidden defaults,
generated IDs, timestamps, model provenance or inferred Capture key.

RECALL: only the requested exact key/topic may be extracted. Execution is existing
exact-key FIND, no semantic/vector retrieval, synonym expansion, hidden kind,
automatic record selection, READ or answer synthesis. Optional kind is explicit
user control only, under existing validity/conflict semantics.

ADD/READ: an explicitly named list MUST occur in the original request in a list-
destination construction, not merely somewhere in payload. Freeze conservative v1
literal role evidence: one unambiguous terminal a la lista <list_id> construction
for ADD; one unambiguous terminal la lista <list_id> construction for READ,
optionally ending in the request's question wrapper. Keywords use section 4's
comparison; fixed keyword spaces are ASCII, identifier slices preserve original
text. Multiple destination constructions are protected/ambiguous. The extracted
list_id must exactly match that construction's identifier after permitted trimming
and pass existing list-ID constraints. An unrelated occurrence in item/value or
quoted instruction cannot satisfy destination evidence. Generic mis pendientes,
mis tareas, esa lista and bare la lista supply NO list ID/default. Model-assisted
list operations cannot acquire a missing original destination from a hidden default
or explicit control as a substitute for original-text evidence. Insufficient role
evidence remains clarification/Unsupported; never guess. Existing deterministic
Sprint 41 generic-list clarification behavior remains unchanged.

## 9. Deterministic command authority and editor

Candidate is DATA only. Only deterministic LUXIOM code constructs final commands:
knowledge store :: ..., knowledge find :: ..., list add ..., list read ... .
Execution interpreter grammar MUST NOT change in Sprint 42. Preserve complete
command maximum 8192 Unicode code points, isolated-surrogate rejection, existing
JSON escaping/closed field sets, list identifier whitespace/:: restrictions,
single-item/no-| constraints and explicit-field conflict semantics. Server returns
validated semantic fields, not model-supplied command text. Existing browser/core
builders combine them with explicit controls; any shared/counterpart construction
requires parity with existing builders and the real Python interpreter.

Final command is visible/editable. User may edit or reject. Send transmits EXACT
visible editor text; no reinterpretation on Send or rebuilding after Send. Invalid,
missing or conflicting fields produce no hidden command. Preserve Sprint 41 Reject,
manual-edit/edit-back, stale/editor retention and Sprint 40 correlation rules.

## 10. Separate non-executing preparation endpoint

Freeze POST /local/intent-preparation through existing loopback interactive app.
Do NOT reuse POST /local/command or cognitive fallback. Request JSON contains
EXACTLY text, a string; reject duplicate/extra keys, invalid types and surrogate/
length violations. No proof, requested_workspace_id, actor, workspace, permissions,
allow_cognitive_fallback or execution token. Server independently validates text,
deterministic recognition/safety eligibility and candidate safety. Protected or
recognized input produces zero provider calls even via direct HTTP.

The endpoint performs no governed action and authenticates/authorizes none. It is
still transport protected. UI opt-in controls whether it is called; it is not an
execution consent or a browser assertion that overrides server safety.

## 11. Transport and loopback provider security

Explicitly extend _StrictInteractiveTransportPolicy to the new POST endpoint;
current path-specific /local/command checks do not automatically cover it.
Require exact existing Host 127.0.0.1:8765 and Origin http://127.0.0.1:8765,
existing strict JSON Content-Type policy and valid runtime X-LUXIOM-CSRF token.
Header names are case-insensitive. Reject duplicate/missing protected headers,
wrong values, media type or CSRF. Existing strict JSON policy permits application/json
with at most its existing optional UTF-8 charset parameter, no broad CORS bypass.
Endpoint is available ONLY through the loopback interactive app, never a non-loopback
listener/public application exposure. Transport rejection occurs before provider use.

No browser-direct Ollama calls, caller-selected provider URL/model, redirects
outside fixed local boundary, remote HTTP(S), network/cloud fallback or dynamically
selected endpoint from user text. The concrete adapter targets explicitly configured
local Ollama loopback service only; remote endpoints are invalid. Disable environment
proxy routing for this local transport; do not follow redirects to escape the
boundary. No OpenAI/Anthropic/Gemini integration. Configuration validation precedes
provider I/O, with bounded sanitized unavailable/failure behavior.

## 12. HTTP dependency and model configuration

During separately authorized implementation, explicitly declare requests>=2.32,<3
as a direct runtime dependency in pyproject.toml. Existing environmental/transitive
availability is insufficient. This contract PR DOES NOT edit dependencies.

Architecture remains provider/model agnostic. Adapter reads model name only from
explicit local configuration, never user input. Absent/unavailable configured model
means provider unavailable. No automatic pull/install/download/substitution.
Native acceptance candidate: qwen3.5:2b-q4_K_M. Secondary qwen3.5:4b-q4_K_M requires
separate authorization and measured headroom. Do not hardcode Qwen in core/domain.
Installed llama3.2:3b is NOT automatically Sprint 42 evidence. Every model download,
generation or benchmark requires separate explicit authorization.

## 13. Provider request bounds

| Limit | Frozen v1 value |
|---|---|
| Original natural input | At most 8192 Unicode code points |
| Accepted provider response body | At most 32768 bytes |
| Provider timeout | At most 30 seconds, bounded overall provider operation |
| Streaming | Disabled |
| Provider calls | At most one per explicit eligible Interpret attempt |
| Retry/repair/background generation | None |

Enforce response-body size while reading, before unbounded buffering/parsing;
body-size limit includes the provider transport envelope. Decoded candidate cannot
escape size/field/input/surrogate checks. No oversized truncation or repair. No
readiness generation or retry after failed model lookup. Server contains blocking
provider work so bounded request handling does not create unbounded pending work.

## 14. Failures and closed preparation service response

Safely handle unavailable Ollama, connection refused, absent model, timeout, HTTP
failure, malformed JSON, invalid schema, unknown intent, duplicate/extra key, prose,
refusal, unsupported result, non-grounded/wrong-role field, oversize field/response,
isolated surrogate and unexpected provider exception. None creates a command unless
ALL validation succeeds. No raw exceptions, prompts/provider internals to UI; no
persistent prompt/response logging; no external fallback or authority downgrade.

Freeze service response as EXACTLY state and candidate. State enum:
candidate_accepted, unsupported, provider_unavailable, provider_failure.
For candidate_accepted, candidate has EXACTLY intent, fields, provenance; intent
is one allowed family, fields are validated/grounded allowed extracted strings,
provenance is exactly local_model_assisted. Partial accepted semantic data is still
not a complete command; explicit completion/clarification remains deterministic.
For every other state candidate is null, no command or hidden executable payload.
unsupported covers protected input and closed provider unsupported/refusal;
provider_unavailable covers missing service/model/configuration;
provider_failure covers timeout/HTTP/provider exceptions and rejected candidates.
Transport errors remain strict HTTP rejections, never candidates or execution results.

No permissions, workspace, actor, proof, repository/memory data or executable
command in service response. UI renders fixed safe state explanations and literal
fields. Previous manual editor text is retained with no-new-command/stale messaging,
never misrepresented as accepted model output.

## 15. Zero preparation-time authority

Prove ZERO preparation-handler repository reads/writes, memory reads/writes,
knowledge reads/writes, gateway execution, permission/membership/workspace/actor
decisions, execution proof usage and cognitive fallback invocation. Inject no such
ports/dependencies into provider or preparation service. Never use helpful
FIND/BROWSE to resolve ambiguity. Runtime startup/storage/bootstrap is NOT described
as I/O-free; this invariant concerns preparation handling specifically.

## 16. Async/correlation and visible provenance

Only one assistance request may be pending per panel/session interaction. Duplicate
Interpret while pending MUST NOT invoke provider again; never queue Send. Correlate
responses to request identity AND current input/control/editor/consent state.
Discard late responses after natural-input change, explicit-field change, toggle
change, Reject, manual editor change, manual edit-back or new interpretation.
A stale response NEVER replaces manual text, restores rejected proposal, clears a
newer proposal or triggers Send. Cancellation may be attempted; identity-based
stale rejection is mandatory even if computation cannot be cancelled. Repeated
explicit attempts are distinct, not automatic retries.

UI visibly distinguishes Deterministic, Local-model assisted, Clarification required,
Unsupported and Provider unavailable/failure. Local-model assisted is proposal
provenance only: never executed, authorized, trusted or verified. Manual editor is
authoritative. Preserve visible focus, keyboard navigation, labels/status and literal
rendering; no user/model innerHTML execution. Preserve Reject including untouched
proposal clearing, manual/edit-back retention and unrelated editor retention for
clarification/Unsupported. Refresh resets opt-in and transient proposal state.

## 17. Send and existing authority

Explicit Send is the ONLY execution boundary. Existing execution envelope remains
EXACTLY proof, requested_workspace_id, text, allow_cognitive_fallback. Add no model-
preparation field. Authentication, principal mapping, explicit workspace, membership
and action permission remain authoritative after Send; live revocation must deny.
Preparation never determines execution success or grants future authority.
Existing cognitive fallback semantics remain post-Send and unchanged. Interactive
runtime continues REASONING_ENABLED=False for that generic reasoning path; local
preparation does not enable CognitiveEngine/ReasoningProvider.

## 18. Required future test/acceptance contract

- Prepared/ClarificationRequired/protected Unsupported each zero model calls;
  opt-in OFF zero; eligible + ON at most one. Direct endpoint protected or
  recognized input zero provider calls; server never trusts caller eligibility.
- Closed JSON shape, duplicate/extra/unknown fields, fifth intent/tool/command
  rejection, arrays/nesting/coercion/prose/trailing data, refusal and malformed
  provider envelopes. Hostile prompt injection remains inert data.
- Literal contiguous grounding with case/Unicode/interior whitespace preservation;
  wrong-role rejection, explicit list destination, no mis pendientes/default list,
  Capture missing metadata/explicit-control conflicts and no inferred provenance.
- Unavailable service/model, refused connection, timeout/HTTP error/exception,
  oversize response/field, surrogate, no retries/repair/cloud fallback, response
  streaming disabled and bounded operation; no new or hidden command on failure.
- Transport exact Host/Origin/CSRF/content type, duplicate/missing headers, closed
  text-only request, loopback/configuration/redirect/proxy safety and no remote I/O.
- Instrument zero repository/memory/knowledge/gateway/authentication/actor/workspace/
  membership/permission access before Send; no execution proof to preparation.
- Session OFF/reset; one pending request, duplicate Interpret, out-of-order/late
  response invalidation for every section 16 cause, Reject/manual edit-back,
  accessible literal provenance/state; no automatic/queued Send.
- Exact visible editor on Send, no reinterpretation/rebuild, unchanged envelope,
  existing auth/workspace/membership/permission denial and live revocation after
  preparation; real Python interpreter parity for all four command families.
- Sprint 41 deterministic corpus/pure-path regression with separate opt-in tests;
  Sprint 40 guided Capture/Recall/Follow-up/Verify coexistence/correlation regression.
- Separately authorized real-model/native Windows/Edge acceptance records versions,
  isolated synthetic database, actual network/provider counters, peak RAM, bounded
  cold/warm latency and extraction/failure behavior. DOM doubles are not native.
- Full governed regression excludes ENTIRE tests/unit/reasoning BEFORE collection
  using --ignore=tests/unit/reasoning; lint excludes it before inspection using
  --extend-exclude tests/unit/reasoning --force-exclude. No foreign import/collection/
  execution/lint. Use isolated external temp/evidence directories.

No tests, model runs or feature acceptance are claimed by this documentation PR.

## 19. Frozen implementation blocks — separate authorization required

| Block | Future scope |
|---|---|
| A | Closed candidate/domain contracts, dedicated eligibility, validator/source grounding, provider-independent tests |
| B | Specialized local adapter, explicit requests dependency, separate endpoint, transport security/failure containment |
| C | Session opt-in UI, deterministic-first integration, provenance, async correlation and manual editor authority |
| D | Security/authority proofs, provider failure matrix, real-interpreter parity, zero pre-Send authority, Sprint 40/41 regression |
| E | Separately authorized real-model setup/evaluation, native Windows/Edge acceptance, full governed regression, release lifecycle |

No Block A or implementation branch before independent contract review and a
separate explicit implementation authorization. Release/setup operations also
require their applicable later authorizations; contract freeze alone grants none.

## 20. Non-goals

No new intent families, task lifecycle, knowledge update/delete, planning expansion,
agent loops, autonomous actions, auto-Send, semantic/vector retrieval, persistent
conversation memory, implicit workspace/permission/provenance/list resolution,
cloud models, internet fallback, mobile/Android/iOS, cloud synchronization,
HealthBridge, Hermes, Spatial UI, voice, billing or Sprint 43 work.
No new execution capability, grammar, schema migration or permissions.

## 21. Foreign custody and documentation lifecycle

Foreign tree tests/unit/reasoning remains untracked, unstaged, unmodified and outside
Sprint 42 scope. Exact known file tests/unit/reasoning/entities/test_user_request.py
has custody SHA-256
45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C.
Classification E. INSUFFICIENT_EVIDENCE. Corrected planning Section D distinguishes
remote empty placeholder/different populated path from local-only snapshot tree
reachability, without claiming exact historical populated provenance. Do not reread,
execute, import, collect, lint, stage, move, rename, modify, delete or copy the foreign
source. Only hash verification remains permitted; no add/delete decision here.

This contract PR changes EXACTLY this contract, LUXIOM_CANONICAL_PROJECT_STATE.md
and docs/knowledge-base/02_CURRENT_STATE.md. Synchronize current planning truth only;
preserve historical release evidence. Calculate this finalized contract SHA-256 and
record it in both state documents and PR body; do not change this contract after
recording without recomputing ALL references. No source/tests/dependencies changed.
Documentation validation: exact three-file scope, expected merged parent, foreign
hash/custody, immutable tag identity, git diff --check. No pytest/Ruff/model run.

After commit, normal push and behavior-contract PR creation: HARD STOP for independent
contract review. Do not merge this PR, implement, edit pyproject.toml, create an
implementation branch or install/download/generate a model.

SPRINT 42 IMPLEMENTATION IS NOT YET AUTHORIZED BY THIS FROZEN BEHAVIOR CONTRACT

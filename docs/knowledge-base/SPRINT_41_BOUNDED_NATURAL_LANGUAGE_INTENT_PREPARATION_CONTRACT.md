# Sprint 41 — Governed Bounded Natural-Language Intent Preparation v1
## Frozen Behavior Contract Candidate v1

Status: Candidate for freeze

Implementation: NOT YET AUTHORIZED

Schema migration: None

New backend capability: None

New endpoint: None

New permission: None

Model/provider use: None

## 1. Authority and checkpoint

This document proposes behavior for review and freeze; it does not claim that
the capability exists or that the contract is already frozen. The user's
authorization covers planning-baseline synchronization and behavior-contract
preparation/freeze lifecycle only. Feature work requires candidate review,
contract freeze and separate explicit implementation authorization.

Planning baseline commit: `73a11e884db9fa22b4a3c1c0ec9ee46c97bccfe8`.
Baseline PR: #72, MERGED through normal two-parent merge
`a0e97c815ed8b295dc9aac460490cefeafee128c`. Ordered parents:
`4f3de7b56001340aba1f39be812eb9b630a07960` and
`73a11e884db9fa22b4a3c1c0ec9ee46c97bccfe8`.

Sprint 40 remains FORMALLY CLOSED, MERGED, TAGGED, BACKED UP, RECOVERY VERIFIED,
with POST-CLOSURE BRANCH CLEANUP COMPLETE and CANONICAL TRUTH FULLY SYNCHRONIZED.
Its annotated tag `governed-sprint-40-complete` remains object
`22044ff154287c000251a16e503807151104e81f`, peeling to release
`3a3b607d94e359a1410f29da894882424fadb6f6`, tree
`7bf9b8478772c75804b1c378c74f8cc00147e1bd`. This contract changes no release
identity and rewrites no historical checkpoint.

Sprint 42 is not authorized. Local Model-Assisted Intent Preparation v1 is
only a possible successor, not a scope commitment or required model adoption.

## 2. Objective

The proposed Sprint 41 capability is one bounded deterministic browser-side
preparer. A user expresses one supported everyday intent in Spanish and receives
visible interpreted intent, explicitly extracted fields, explicitly missing
fields and an exact governed command when representable. Preparation executes
nothing. The existing editable command and separate explicit Send remain visible.
This is the first sprint explicitly on the LUXIOM Demo v1 product-usefulness path.

## 3. Architectural boundary

Human text -> pure deterministic browser preparation -> preparation result ->
exact visible editor command if Prepared -> optional edit/reject -> explicit
Send -> existing POST /local/command -> application gateway -> authentication ->
principal mapping -> workspace -> membership -> existing deterministic command
interpreter -> existing permission policy/capability -> repository -> existing
structured result projection.

Interpret/Prepare MUST NOT call POST /local/command, the gateway, routing service,
coordinator, repositories, memory/knowledge storage, providers, provider readiness,
Ollama, CognitiveProcessor, ReasoningProvider, cognitive fallback or external
network. It makes ZERO application requests, persistence operations, repository
reads, provider/readiness calls, fallback calls and authorization decisions.
No identity, workspace or permission authority moves into the browser.

Existing typed intents and command grammar remain execution contracts.
The application gateway continues to own semantic intent/result correlation.
Preparation state and browser validation cannot replace downstream validation.

## 4. Closed preparation result

Exactly three semantic outcomes exist. These are preparation-only values, not
LocalCommandApplicationResult, TextRoutingResult or execution projections.
Transport/API result contracts are unchanged; no preparation endpoint is added.

| Outcome | Required meaning and payload | Command/editor effect |
|---|---|---|
| Prepared | Exactly one supported intent, complete valid explicit fields and one exact serialized command | May replace the visible editor with that exact command |
| ClarificationRequired | One recognized candidate intent, partial explicit fields, ordered missing/invalid/conflicting field names and clarification text | No complete or hidden executable command; editor unchanged |
| Unsupported | Stable reason and explanatory literal text; no selected executable action | No command; editor unchanged |

Prepared never means authorized, executed, persisted or successful. No fourth
semantic variant is permitted. Stale, edited and pending are UI presentation
states, not additions to this union. Unsupported must not be presented as a
successful interpretation. Failure never automatically enters cognitive fallback.

## 5. Exact supported corpus and recognition

Exactly four intent families are supported. One interaction prepares at most
ONE operation. The following templates are the complete v1 positive corpus;
examples elsewhere do not add synonyms, syntax or extra templates.

| Intent | Full-input template | Extracted payload |
|---|---|---|
| CAPTURE_KNOWLEDGE | `Recuerda que <value>` | value |
| CAPTURE_KNOWLEDGE | `Guarda que <value>` | value |
| CAPTURE_KNOWLEDGE | `Anota que <value>` | value |
| RECALL_KNOWLEDGE | `Qué te dije sobre <key>` | key |
| RECALL_KNOWLEDGE | `Qué sabes de <key>` | key |
| ADD_FOLLOW_UP | `Agrega <item> a la lista <list_id>` | item, list_id |
| ADD_FOLLOW_UP | `Añade <item> a la lista <list_id>` | item, list_id |
| ADD_FOLLOW_UP | `Agrega <item> a mis pendientes` | item; list_id missing |
| ADD_FOLLOW_UP | `Añade <item> a mis pendientes` | item; list_id missing |
| READ_FOLLOW_UP | `Qué hay en la lista <list_id>` | list_id |
| READ_FOLLOW_UP | `Muéstrame la lista <list_id>` | list_id |
| READ_FOLLOW_UP | `Qué tengo pendiente` | list_id missing |

Recognition is anchored to the whole request, never a substring search for a
trigger. Fixed keyword separators are one ASCII space (U+0020). Extra internal
keyword whitespace and unlisted synonyms are Unsupported. Payload may contain
interior whitespace/newlines where the existing command permits them.

Only for keyword comparison, map ASCII A-Z and ÁÉÍÓÚÜÑ to their lowercase
counterparts. Do not use locale-dependent comparison, fuzzy matching, scoring,
ranking, accent removal or Unicode normalization. Accented keywords are required
as shown; this mapping never rewrites payload. Recognition and extraction must
be separately testable, with original payload slices retained.

Ignore outer Python-str.strip whitespace for matching. Its exact set is
U+0009-U+000D, U+001C-U+0020, U+0085, U+00A0, U+1680, U+2000-U+200A,
U+2028-U+2029, U+202F, U+205F and U+3000.
For Recall and the two `Qué` Read templates only, permit one optional leading
`¿` and one optional trailing `?`, independently. These are syntactic wrappers,
not part of the key/list ID. Literal boundary question marks in a Recall key
are outside this bounded input syntax; use existing explicit FIND controls.
Do not strip periods or other payload punctuation.

ADD requires exactly one recognized destination separator (` a la lista ` or
the final suffix ` a mis pendientes`). Multiple destination separators are
Unsupported with reason `ambiguous_structure`; do not choose a split silently.
For an unambiguous recognized template with a blank required placeholder,
return ClarificationRequired for that field, not Prepared. Empty overall input
is Unsupported. A prefix without enough structure to identify one template is
Unsupported. No recognition reads previous conversation or backend data.
For empty-value recognition specifically, `Recuerda que`, `Guarda que` and
`Anota que` identify Capture with missing value; `Qué te dije sobre` and
`Qué sabes de` identify Recall with missing key; `Qué hay en la lista` and
`Muéstrame la lista` identify READ with missing list_id. Apply the same keyword
comparison and allowed question wrappers. ADD with an intact destination
separator and a whitespace-only item or list_id identifies those missing fields.
Bare `Agrega` or `Añade` without a destination structure remains Unsupported.

## 6. Stable rejection and clarification rules

Apply these gates in order; a later match cannot override an earlier rejection:

1. Non-string, empty/whitespace-only, oversized input or isolated surrogate:
   Unsupported (`invalid_input`). Natural input is capped at 8192 Unicode code
   points; this does not relax the complete-command limit.
2. A top-level negation or condition outside the positive corpus is Unsupported
   (`unsupported_request`). In particular `No recuerdes que ...` never becomes
   Capture. A negative statement inside `Recuerda que ...` remains literal value.
   Within otherwise matching requests, standalone `si` or `cuando` also returns
   Unsupported (`conditional_request`), conservatively even inside payload.
   Use the standalone boundaries and keyword comparison defined for pronouns
   below. Do not interpret a condition or schedule a conditional operation.
3. Whole quoted/example instructions or explanatory prefixes are Unsupported
   (`unsupported_request`): `"Recuerda que ..."` and `Por ejemplo: Recuerda que ...`
   do not match. Quotes/HTML/JSON inside a matched payload remain literal data.
4. Multiple supported actions are Unsupported (`multiple_actions`), never a
   partial Prepared or a guessed first action. For this bounded corpus, reserve
   the connectors ` y `, ` luego `, ` después `, ` entonces ` and `; ` when followed
   by one of `recuerda`, `guarda`, `anota`, `agrega`, `añade`, `agrégalo`, `añádelo`,
   `muéstrame` or `qué` plus a space, using keyword comparison above. Reject these
   combinations even within payload, conservatively. `Recuerda X y agrégalo a la
   lista Y` is Unsupported. Unlisted combined-request forms have no support promise.
5. Pronoun/context resolution is excluded. Anaphoric request verbs such as
   `agrégalo` are outside the corpus. Payload containing standalone `esto`, `eso`,
   `aquello`, `ello`, `él`, `ella`, `ellos` or `ellas` is Unsupported
   (`context_reference`), conservatively even if an operator could infer a
   referent. Standalone means bounded by start/end or a non-letter/non-digit;
   compare keywords using the mapping above. No antecedent is resolved.
6. No unique template, or conflicting destination structure: Unsupported
   (`unsupported_request` or `ambiguous_structure`). Conditional/multi-step
   behavior is never inferred from payload; it cannot add operations.
7. One candidate with missing, invalid or conflicting explicit fields:
   ClarificationRequired. Report fields in the intent's order below. Invalid
   fields require user correction, not silent repair. A conflicting field must
   be made consistent by the user before preparation can succeed.
8. A complete candidate that cannot fit existing grammar or serialized length:
   Unsupported (`unrepresentable`). Otherwise Prepared.

These conservative lexical limits deliberately reject some ordinary Spanish.
They are a bounded contract, not general Spanish understanding. All other
requests are Unsupported and remain available to the existing manual UI.

## 7. Explicit-field completion

Recognized payload values come from exact user text; visible controls may supply
missing fields. No metadata is inferred from entity names, grammatical meaning,
identity, browser/session context or prior results. Extracted fields and missing
fields must be visible. Optional unset fields are omitted, never invented.

If both natural text and an explicitly entered control supply the same field,
their values must agree after existing edge trimming; otherwise return
ClarificationRequired for that field. Do not silently choose either source.
The user may correct the natural text or control and prepare again. Blank
controls do not override extracted values. Intent selection is not a way to
bypass the supported text corpus. Reused controls must not silently contribute
old values: only visible fields explicitly supplied/selected for the current
proposal count. Refresh/reset clears preparation state; no cross-session defaults.

Missing, invalid and conflicting names use stable field order:
Capture: record_id, kind, key, value, source_type, source_reference;
Recall: key, kind; ADD: list_id, item; READ: list_id.
An omitted optional Recall kind is not missing. Corrections require an explicit
Interpret/Prepare action; editing a field never auto-prepares or sends.

## 8. CAPTURE_KNOWLEDGE / STORE

Capture may extract only the explicit statement/value from its template.
It MUST NOT invent record_id, kind, key, source_type or source_reference.
For `Recuerda que MedSupply entrega los martes.`, value is
`MedSupply entrega los martes.`; all five metadata fields require explicit input.
There is no automatic kind=fact, key=MedSupply or generated ID default.

Existing STORE requires exactly six nonblank strings: record_id, kind, key,
value, source_type, source_reference. Kind is exactly `fact`, `concept` or
`state`, selected/provided explicitly. No extra JSON fields are permitted.
Workspace is supplied by governed execution, never inserted in STORE JSON.
Until all six fields are explicit and valid, return ClarificationRequired.
Once complete, serialize exactly the existing `knowledge store :: {JSON}`
with those six fields in the order above. Existing edge trimming remains;
interior user text must not be normalized, rewritten or summarized.

Provenance is an explicit user assertion, not verified identity. No `chat`,
current session, timestamp, device, authenticated user, runtime or model identity
may be inserted silently. No system-generated provenance policy is introduced.
The preparer does not check ID uniqueness or persistence; conflict/idempotence
continues to be decided by existing STORE after Send.

## 9. RECALL_KNOWLEDGE / FIND

Recall prepares exact-key discovery only: `knowledge find :: {JSON}` with
explicit `key` and optional explicitly provided `kind`. JSON field order is key,
then kind if supplied. `¿Qué te dije sobre MedSupply?` extracts key `MedSupply`.
Do not expand synonyms, casefold keys, perform substring/fuzzy/vector search,
use model retrieval or promise everything related to a concept.

An empty key requires clarification. An invalid supplied kind requires
clarification; it cannot be silently dropped. No queries occur during preparation.
FIND does not complete READ. Existing selection of a returned record, preparation
of READ and separate Send remain separately governed. This intent does not
automatically choose a record, READ it, browse additional pages or synthesize an
answer from results. Existing result projections remain unchanged.

## 10. ADD_FOLLOW_UP / one list ADD

Explicit-list templates require list_id and exactly one item. The generic
`Agrega llamar a MedSupply a mis pendientes` recognizes ADD and extracts
`llamar a MedSupply`, but requires ClarificationRequired for list_id until the
user explicitly supplies/selects a concrete ID. `mis pendientes` is not an ID,
default destination or authority-bearing alias.

Serialize only `list add <list_id> :: <item>`. Preserve Sprint 40 preparation
constraints: list_id is nonempty, contains no Python whitespace and no `::`;
item is nonblank, exactly one item, contains no `|`. Trim item edges as existing
preparation does; preserve interior text. Invalid ID/item fields require
clarification. Literal `|` is not escapable in the existing grammar: report it
as invalid item requiring clarification, never split or remove it silently.
No escaping grammar, multiple items, due dates or scheduling are introduced.

## 11. READ_FOLLOW_UP / list READ

`¿Qué hay en la lista <list_id>?` and `Muéstrame la lista <list_id>` prepare
`list read <list_id>` only with an explicit valid ID. Apply the same safe list-ID
constraints as ADD. `¿Qué tengo pendiente?` returns ClarificationRequired for
list_id until explicitly supplied/selected. No default tasks list or aggregate
list discovery is introduced. Preparation does not assert the list exists or
contains items. Existing empty-list behavior remains an execution result.

## 12. Serialization, representability and Unicode

Knowledge payloads must use the existing JSON serialization approach, never
string interpolation of unescaped JSON values. Quotes, backslashes, newlines,
HTML, command-like text and `::` inside JSON string values remain literal data.
No trailing JSON, extra fields or hidden second command may be appended.
List commands use the existing delimiter grammar and its constraints above.
Do not add escaping or modify the backend parser to make payloads representable.

Each Prepared complete command must be at most 8192 Unicode code points,
including prefix and serialized JSON. Count Unicode code points, not UTF-16
code units; reject isolated surrogates in input/explicit fields/command.
Preserve combining characters and interior whitespace without normalization.
Only existing Python-compatible edge trimming is allowed; no locale behavior.
Serialization overflow is Unsupported (`unrepresentable`), without truncation.
Every Prepared family must have parity evidence using the real existing Python
command interpreter: same operation and fields after its documented trimming.

## 13. Zero requests and persistence

Prepared, ClarificationRequired and Unsupported all cause zero fetch calls,
application requests, repository calls, storage mutations, provider/model calls
and readiness calls. No helpful FIND/BROWSE resolves ambiguity before Send.
Do not read backend or browser persistent storage for interpretation context.
No new persistence for natural input, proposals, clarifications, conversation,
history or intent state; browser-memory state may be lost on refresh.
Existing knowledge/list persistence is reached only after governed Send.

## 14. Editor authority, rejection and invalidation

Prepared may replace only the visible editable command with its exact command.
Send submits the exact editor text at that explicit action. It MUST NOT re-run
natural-language interpretation or rebuild from hidden preparation state.
Manual edits are authoritative, even if they differ from the original proposal.
Mark that proposal edited/stale immediately; never restore the original on Send.

Changing natural input, clarification controls or relevant selections immediately
invalidates the old proposal. Re-preparation is required before claiming a
proposal corresponds to current inputs. This invalidation makes zero requests.
Retain editor text with a visible stale indication; do not silently substitute
or send it. Send remains the existing manual execution path and may still send
the visible editor after explicit user review; stale is not new authorization.

ClarificationRequired/Unsupported leave editor text unchanged and explicitly
say no new command was prepared. Rejection dismisses the proposal without
sending or persistence. If the editor still exactly equals the rejected prepared
command, clear it; if manually edited, preserve the text and mark it manual.
Never retain a hidden executable proposal. Input/prepare/reject controls cannot
submit the command form. While a governed request is pending, lock new preparation
and proposal replacement consistently with existing controls; never queue Send.

## 15. Sprint 40 coexistence

Capture -> Recall -> Follow-up -> Verify remains available as the existing
guided workflow. Natural-language preparation is a parallel entrypoint.
Replacing the command editor must clear any incompatible pending guided
correlation using existing invalidation semantics. Preparation cannot complete
Sprint 40 stages, fake results, seed hidden success or retain authority from
guide state. Only existing correlated governed results may complete stages.
No automatic READ, next-page request, ADD or verification follows a proposal.

## 16. Model, fallback and authorization

Sprint 41 uses no model, Ollama, ReasoningProvider or CognitiveProcessor for
interpretation. It does not reinterpret the existing fallback checkbox.
Existing execution fallback semantics remain unchanged; preparation failure
returns ClarificationRequired or Unsupported, never automatic cognitive fallback.

Every Send still passes authentication, mapping, workspace, membership and
action-permission checks. Prepared may fail at Send; prior success grants no
future authority. Interpret must not accept or derive proof, actor/workspace
claims or permissions from natural text. No cross-workspace interpretation reads.
Existing projections, denials, revocations and local terminal behavior remain.

## 17. Hostile text and minimum accessible UI

Render all user-controlled natural text, fields and clarification content as
literal text, never innerHTML-style markup or script. Command/prompt-like text
inside a payload remains data. Model prompt injection is not a new execution
surface because there is no model use; hostile text still requires literal
rendering, delimiter validation and explicit review. Imperative wording grants
no authority. Never execute browser/shell code from input.

Minimum UI: one labelled natural-language textarea, one Interpret / Prepare
button, visible intent/extracted fields/missing fields, explicit clarification
controls and the exact command in the existing editor when Prepared. Existing
operation-specific controls may be reused for explicit completion. Add no whole
UI redesign, external UI dependency or remote assets.
Require keyboard-only navigation, visible focus, label association, appropriate
status announcements and keyboard button activation. Interpret/Prepare and Send
must be visually and semantically distinct, with no implicit submit from
preparation controls. Status must distinguish proposed, stale and executed data.

## 18. Automated acceptance required after separate authorization

The future implementation must demonstrate all of the following; this document
does not claim that any new feature test has run or passed:

1. All four intent families and every exact positive template, including keyword
   case mapping, question wrappers and intentional unsupported variants.
2. Closed result invariants, ordered missing/invalid/conflicting fields and
   deterministic precedence for all stable rejection reasons.
3. Capture without metadata never Prepared; no invented record ID, kind, key,
   provenance, timestamp or authenticated identity.
4. All six explicit STORE fields and kinds; exact FIND key/optional kind; no
   semantic recall claim or automatic READ.
5. Explicit-list ADD and READ; generic pending forms require list_id; explicit
   controls cannot supply hidden retained defaults or silently resolve conflicts.
6. Negation, quoted/example instructions, multiple actions, pronouns, conditional
   requests, unsupported text, empty/whitespace payloads and ambiguous separators.
7. Hostile literal HTML/script/JSON/commands, quotes/backslashes/newlines,
   Unicode/combining-text preservation and Python-compatible whitespace edges.
8. `|` item and `::` list-ID rejection without splitting/escaping; no extra JSON
   fields; isolated surrogates and complete-command 8192-code-point boundaries.
9. Zero fetch/application/repository/provider/model/readiness/fallback/storage
   calls for all three outcomes, clarification, edit, invalidation and rejection.
10. Exact editor command on Send, manual-editor authority, natural-input/explicit
    field invalidation, no reinterpretation/rebuild on Send and pending locking.
11. Real existing Python interpreter parity for every Prepared command family;
    backend contracts and list/knowledge structured projections unchanged.
12. Existing gateway authentication/mapping/workspace/membership/action permission
    and revocation still enforced after Send, including denial with valid proposal.
13. Sprint 40 guided-state coexistence/invalidation and complete journey regression.
14. Full governed-suite regression excluding the ENTIRE foreign
    `tests/unit/reasoning/` tree before collection. Never import/execute/read its
    foreign file; custody permits only Get-FileHash on that file.

## 19. Native Windows browser acceptance required later

Future acceptance must use a real native browser on Windows, record browser
name/version, Windows version, date and isolated synthetic database. DOM doubles
are automated evidence, not substitutes for native acceptance. Required scenarios:

1. Capture phrase recognized.
2. Missing STORE metadata produces clarification with zero requests.
3. Explicit completion prepares exact STORE.
4. Recall phrase prepares exact FIND.
5. ADD with explicit list prepares exact ADD.
6. `mis pendientes` requires explicit list clarification.
7. Explicit READ prepares exact list READ.
8. Generic pending question requires list clarification.
9. Unsupported text prepares no command.
10. Negated instruction never prepares its opposite action.
11. Hostile literal text renders safely.
12. Natural-input editing invalidates the prior proposal.
13. Manual editor edits remain authoritative on Send.
14. Interpret performs zero application requests.
15. Send performs the existing governed request with exact editor contents.
16. Wrong proof or missing/revoked permission fails normally.
17. Existing Sprint 40 guided workflow still works.
18. Keyboard-only path, focus and announcements work.

No native scenario or feature test is authorized by this candidate commit.

## 20. Likely future implementation surface and blocks

Planning only, not an implementation allowlist or authorization:

- `app/api/static/local_ui/app.js` and `index.html` for pure preparation/UI.
- `app/api/static/local_ui/styles.css` only if materially required.
- `tests/unit/api/test_local_interactive_ui.py`, a focused Sprint 41 browser
  harness and existing interpreter-based parity tests.
- Existing interpreter/gateway/capability modules are reference surfaces; no
  backend behavioral change, endpoint or schema migration is expected.

| Future block | Proposed work, NOT authorized here |
|---|---|
| A | Pure bounded preparer, closed preparation contract and serializer parity |
| B | Minimal natural-language UI and explicit clarification |
| C | Stale-input/editor/Sprint-40 correlation invalidation |
| D | Security, real-interpreter parity, authorization regression and zero-request/provider proof |
| E | Native acceptance, full regression and documentation/release lifecycle |

## 21. Explicit non-goals and next gate

No autonomy, implicit Send, multi-step planner, agent loop, persistent
conversation, pronoun/context resolution, semantic/vector retrieval, knowledge
edit/delete, calendar/email/browser automation, external connectors, Hermes,
Spatial implementation, HealthBridge coupling, production authentication
redesign, new workspace/permission authority, schema migration, backend endpoint,
model/provider use, provider-specific architecture or unrestricted free-form agent.
No automatic provenance, record IDs, implicit/default list, automatic discovery
or data reads during interpretation, new command grammar, escaping redesign,
generic multilingual NLU or model-assisted interpretation in Sprint 41.

Next gate: independent review of this pushed candidate, before any contract PR.
This branch must remain pushed and unmerged without a PR at this execution's
end. Candidate review and contract freeze precede a separate explicit feature
implementation authorization. Neither baseline merge nor candidate publication
grants that authorization or starts Sprint 42.

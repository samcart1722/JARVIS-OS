# Sprint 40 — Guided Local Capture–Recall–Action Experience v1
## Frozen Behavior Contract Candidate v1

**Status:** Candidate for freeze
**Implementation:** NOT YET AUTHORIZED
**Schema migration:** None
**New backend capability:** None
**New endpoint:** None
**New permission:** None
**Model/provider use:** None

## 1. Objective

Sprint 40 adds one guided browser journey that makes existing governed LUXIOM capabilities understandable as a coherent local experience.

The user must be able to:

1. explicitly capture knowledge;
2. rediscover it through FIND or BROWSE;
3. explicitly READ the selected record;
4. explicitly author and prepare a follow-up list item;
5. execute the list ADD;
6. READ the list to verify persistence.

The workflow is guidance and command preparation only.

It never becomes a new authorization, execution, orchestration, reasoning, or persistence authority.

---

## 2. Architectural boundary

The guided experience lives at the presentation layer of `/local/ui`.

Execution remains:

`/local/ui`
→ existing `POST /local/command`
→ application gateway
→ authenticated routing
→ principal mapping
→ explicit workspace
→ membership admission
→ deterministic interpretation
→ permission policy
→ local capability
→ existing repository
→ existing closed projection.

The guided UI must never bypass or duplicate these boundaries.

---

## 3. Existing operations reused

### Knowledge

- STORE
- READ
- FIND
- BROWSE
- BROWSE-AFTER

### Lists

- ADD
- READ

No existing command grammar changes.

No new command operation is introduced.

---

## 4. Guided journey

The UI presents four understandable stages:

### Stage A — Capture

Purpose:

Save explicitly supplied knowledge.

User supplies the existing STORE fields:

- `record_id`
- `kind`
- `key`
- `value`
- `source_type`
- `source_reference`

Allowed kinds remain exactly:

- `fact`
- `concept`
- `state`

The guide uses the existing knowledge serializer to prepare:

`knowledge store :: {...}`

Preparation performs zero requests.

The user must review and explicitly press **Send**.

A successful STORE projection may mark Capture as completed.

Preparation alone must never mark Capture as completed.

A failed request must never mark Capture as completed.

A successful unrelated command must never mark Capture as completed.

---

### Stage B — Recall

Purpose:

Rediscover previously stored knowledge.

The user may use:

- FIND by explicit key and optional exact kind; or
- BROWSE; or
- BROWSE-AFTER when more records exist.

The guide may expose these as task-oriented controls rather than requiring command grammar knowledge.

Preparation performs zero requests.

Explicit Send remains required for every request.

A successful FIND/BROWSE/BROWSE-AFTER projection may populate selectable records.

Selecting a record does not read it automatically.

Selection may only prepare a READ command.

The user must explicitly Send the READ command.

Only a successful READ projection for the intended selected `record_id` completes Recall.

BROWSE permission never implies READ permission.

---

## 5. Browse continuation

Existing Sprint 39 semantics remain unchanged.

When a successful BROWSE or BROWSE-AFTER result is truncated:

- the UI may offer **Prepare next page**;
- the anchor is the exact last structured `record_id`;
- preparation performs zero requests;
- the prepared editor remains user-editable;
- explicit Send performs the next request;
- authorization is reevaluated.

No cursor, snapshot, page history, Previous feature, total count, or automatic fetch is added.

---

## 6. Stage C — Follow-up Action

“Action” means only an explicitly user-authored list item.

It does NOT mean:

- autonomous planning;
- inferred tasks;
- model-generated tasks;
- autonomous execution;
- durable linkage between knowledge and task;
- agent orchestration.

The user supplies:

- `list_id`
- `item`

Sprint 40 supports exactly one guided follow-up item per preparation.

The existing backend grammar remains authoritative:

`list add <list_id> :: <item>`

### list_id rules

The prepared `list_id` must:

- be a string;
- contain non-whitespace text;
- contain no whitespace;
- contain no `::` delimiter;
- remain one backend list identifier token.

Invalid IDs fail during preparation.

The guided UI rejects `::` before preparation succeeds. It does not escape,
rewrite, or split the identifier. This prevents a value such as
`project::tasks` from being parsed by the existing interpreter as list
`project` with altered item text.

No request is sent.

### item rules

The guided item must:

- be a string;
- contain non-whitespace text;
- be explicitly authored by the user;
- contain no `|` delimiter.

The `|` character is rejected because the existing interpreter uses it to separate multiple list items and silently allowing it would change the user's intended single follow-up into multiple items.

Outer whitespace may be normalized according to the existing list grammar.

Interior whitespace and Unicode text remain preserved.

Sprint 40 does not introduce escaping or a new list grammar.

The UI prepares:

`list add <list_id> :: <item>`

At successful guided ADD preparation, the guide retains in browser memory:

- the intended `list_id`;
- the expected item after the same outer-whitespace stripping used by the
  existing list grammar.

These values are non-authoritative correlation state only. They are not
persisted and grant no authority.

If the command editor is manually changed after guided ADD preparation and
before Send, the pending Stage C correlation is invalidated. The edited command
remains authoritative and may execute, but that Send cannot complete Stage C.
The user must re-prepare the guided follow-up to establish a new correlation.

Preparation performs zero requests.

Explicit Send is required.

Only a successful existing list ADD projection may mark Follow-up as recorded
when:

- the projection `list_id` exactly matches the retained intended `list_id`; and
- the retained expected item appears exactly in either `added` or
  `already_present`.

The exact Stage C item check uses the current ADD projection, which reports the
submitted item spelling in `added` or `already_present`, including a
case-equivalent duplicate request.

On successful Stage C completion, the expected item remains in browser memory
for Stage D verification.

The guide must not claim a durable semantic relationship between the knowledge record and list item.

Any visual reference to the selected knowledge record is transient presentation context only.

---

## 7. Stage D — Verify Follow-up

The user may prepare:

`list read <list_id>`

The existing grammar remains authoritative.

Preparation performs zero requests.

Explicit Send is required.

When the guide prepares the Stage D list READ, verification is bound to the
retained intended `list_id` and expected item from the successful Stage C.

If the command editor is manually changed after this guided READ preparation
and before Send, the pending Stage D correlation is invalidated. The edited
command may execute, but that Send cannot complete Stage D. The user must
re-prepare the guided list READ.

Only a successful READ list projection completes verification when:

- the returned `list_id` exactly matches the retained intended `list_id`; and
- at least one returned item is casefold-equivalent to the retained expected
  item.

For this contract, two items are casefold-equivalent when applying Python
`str.casefold()` to each produces equal strings. No additional Unicode
normalization, trimming, locale-sensitive collation, or fuzzy comparison is
allowed.

This comparison rule intentionally matches the existing SQLite list duplicate
policy. The browser implementation must use a deterministic UI-only comparator
validated against Python `str.casefold()` parity vectors; locale-sensitive
browser comparison alone is insufficient.

Example: an expected item `GRAPES` verifies successfully when the persisted READ
projection contains `grapes`.

If the expected item is absent under this comparison rule, Stage D remains
incomplete even when the list ID matches and even when Stage C previously
succeeded.

Expected-item presence is proven only from the returned structured list
projection.

It must not infer success from:

- command preparation;
- editor contents;
- prior ADD success alone;
- DOM state left from an earlier response.

---

## 8. Prepare versus Send

This invariant is mandatory across the entire guided workflow.

### Prepare

May:

- validate fields;
- serialize a command;
- replace the editor command;
- update guidance text;
- clear stale projections;
- move focus.

Must NOT:

- call fetch;
- execute a command;
- authorize;
- mutate storage;
- claim execution success.

### Send

The existing Send action remains the sole browser execution boundary.

Each Send:

- submits the exact current editor text;
- performs one governed request;
- independently authenticates and authorizes;
- may succeed or fail regardless of guide state.

Manual editor changes are authoritative.

Guided fields must never silently overwrite the editor at Send time.

---

## 9. Manual-edit authority

After any preparation, the user may manually edit the command.

The exact editor text at Send is authoritative.

If the user changes a prepared command into a different valid command:

- that different command executes;
- the guide must inspect the structured response;
- the originally prepared guided step must not be marked complete unless the returned operation and relevant identifiers match that step.

The guide must never advance from intent alone.

For Stage C and Stage D specifically, any manual editor change after their
guided preparation invalidates the pending guided correlation for that step.
The edited command remains executable because the editor is authoritative, but
the resulting Send cannot advance that guided step. Re-preparation is required
before guided completion can occur.

---

## 10. Result correlation

Guide progression must use structured existing response projections.

It must not reparse the submitted command to establish backend success.

Examples:

- Capture completes only from a valid successful knowledge STORE projection.
- Recall completes only from a successful knowledge READ projection matching the selected record ID.
- Follow-up completes only from a successful list ADD projection whose
  `list_id` matches the retained intended list ID and whose `added` or
  `already_present` contains the retained expected item exactly.
- Verify completes only from a successful list READ projection whose `list_id`
  matches the retained intended list ID and whose returned `items` contains at
  least one item casefold-equivalent to the retained expected item under the
  Stage D comparison rule.

If correlation is absent or mismatched, the governed request result may still be displayed normally, but the guided step remains incomplete.

---

## 11. Guide state

Guide state is browser-memory presentation state only.

It is not persisted.

It carries no authority.

It must be safe to lose on refresh.

At minimum the guide distinguishes:

- not started;
- ready;
- prepared;
- pending;
- completed;
- failed / needs retry.

A prepared state is never equivalent to completed.

A pending request locks guided controls consistently with existing request-pending behavior.

---

## 12. Reset and stale-state behavior

Changing guided operation/input after a completed or prepared state must not leave stale success visible as current truth.

Preparation must clear incompatible stale projections before the next Send.

Request start must clear stale projections.

Disconnect/local fetch failure must not erase the user's editor text.

Failure must not fabricate completion.

A new successful unrelated operation must not complete a previous guided step.

---

## 13. Proof handling

Existing proof behavior remains unchanged.

Sprint 40 does not persist proof material.

Existing proof clearing after request construction remains preserved.

Repeated proof entry may remain necessary in this development UI.

No session or credential redesign is authorized.

---

## 14. Workspace

The existing development workspace remains the governed workspace used by the local interactive runtime.

The guide may display the current development workspace as context.

It must not claim new workspace discovery, administration, or authorization.

Workspace selection remains owned by existing runtime/application boundaries.

---

## 15. Authorization

No new permissions are created.

Every explicit Send uses existing permission checks.

Relevant permission separation remains intact.

Examples:

- BROWSE does not authorize READ.
- READ does not authorize STORE.
- knowledge permissions do not authorize list ADD.
- successful previous requests do not authorize future requests.

Revocation inside a running session must be respected according to current behavior.

Sprint 40 must not claim durable revocation across development bootstrap where existing bootstrap behavior recreates configured development grants.

---

## 16. Local-first guarantee

The complete guided happy path must require:

- no Internet;
- no external model;
- no local model;
- no provider call;
- no provider-readiness call;
- no cognitive fallback.

Only existing loopback application requests are required.

Cognitive fallback remains outside the Sprint 40 guided workflow.

---

## 17. Persistence demonstration

Using the same isolated SQLite database:

1. STORE knowledge successfully.
2. ADD the follow-up successfully.
3. stop the development runtime.
4. start a fresh process against the same isolated database.
5. READ the knowledge.
6. READ the list.
7. verify both persisted results.

This is a demonstration of durable local persistence, not synchronization.

---

## 18. Security and rendering

All returned user-controlled strings must continue to be rendered as text, not interpreted HTML.

No remote UI resources.

Existing Host, Origin, CSRF, CSP, no-store and loopback protections remain unchanged.

No CORS expansion.

No public server exposure.

---

## 19. Accessibility and usability acceptance

The guided experience must be usable with:

- mouse;
- keyboard-only navigation;
- visible focus;
- Enter/Space activation where appropriate.

The workflow must remain understandable without memorizing command syntax.

The editor remains visible and inspectable so execution remains transparent.

---

## 20. Native browser acceptance

Sprint 40 requires real native browser acceptance on Windows.

Record:

- browser name;
- browser version;
- Windows environment;
- isolated synthetic SQLite database;
- test date.

Required native scenarios include:

1. Capture preparation causes zero requests.
2. Capture explicit Send succeeds.
3. FIND recall path.
4. BROWSE recall path.
5. BROWSE-AFTER continuation.
6. selected-record READ requires separate Send.
7. Follow-up preparation causes zero requests.
8. Follow-up ADD succeeds.
9. list READ verifies item.
10. manual editor change remains authoritative and invalidates pending
    Stage C/Stage D guided correlation until re-preparation.
11. wrong proof fails without guided false success.
12. revoked applicable permission fails during the running session.
13. disconnect/local request failure recovery.
14. keyboard-only workflow.
15. refresh safely loses guide state without losing durable data.
16. fresh-process persistence verification.
17. `list_id` containing `::` is rejected during preparation with zero requests.
18. Stage D remains incomplete when the expected item is missing.
19. a case-equivalent duplicate is verified using the frozen casefold rule.

This Sprint 40 acceptance also re-exercises the inherited Sprint 39 browse-after native behavior.

It does not retroactively rewrite Sprint 39's historical `NATIVE ACCEPTANCE NOT EXECUTED` release record.

---

## 21. Automated acceptance

Automated tests must cover at least:

- guided state transitions;
- zero fetch during preparation;
- exactly one request per explicit Send;
- exact editor payload submission;
- manual-edit authority;
- list ADD preparation;
- list READ preparation;
- list ID validation;
- rejection of `::` in a guided `list_id` before any request;
- real-interpreter parity for the delimiter-collision vector
  `list_id = project::tasks`, proving the guard prevents first-`::` misparsing;
- rejection of `|` in a single guided follow-up item;
- Stage C correlation to the exact expected item in `added` or
  `already_present`;
- manual ADD-editor change invalidating Stage C completion until re-preparation;
- manual READ-editor change invalidating Stage D completion until re-preparation;
- Stage D remaining incomplete when the expected item is absent;
- Stage D acceptance of a case-equivalent duplicate such as expected `GRAPES`
  versus persisted `grapes`;
- deterministic browser casefold parity with Python `str.casefold()`, including
  at least one non-ASCII casefold-sensitive vector;
- whitespace behavior;
- Unicode handling;
- pending locking;
- stale-result clearing;
- failed-request state;
- projection correlation;
- hostile literal text rendering;
- existing STORE/READ/FIND behavior;
- existing BROWSE behavior;
- existing BROWSE-AFTER behavior;
- existing list behavior;
- real interpreter parity for generated list commands;
- real authenticated HTTP flow using temporary SQLite;
- fresh-process persistence proof;
- zero observed provider/readiness/cognitive-fallback calls for the supported guided flow.

The unrelated foreign test remains excluded.

---

## 22. Likely implementation surfaces

Expected primary surfaces:

- `app/api/static/local_ui/index.html`
- `app/api/static/local_ui/app.js`
- `app/api/static/local_ui/styles.css`
- focused Python UI tests
- existing/new Node browser harness for Sprint 40
- optional acceptance documentation

Backend Core, gateway, command interpreter, permissions, schema, repositories and CognitiveEngine should require no feature modification.

If implementation discovers that a backend contract must change, STOP and reopen architecture review rather than silently expanding Sprint 40.

---

## 23. Explicit non-goals

Sprint 40 does not include:

- natural-language command interpretation;
- LLM command parsing;
- model enablement;
- model reasoning over durable knowledge;
- semantic retrieval;
- knowledge edit;
- knowledge delete;
- knowledge-to-task persistent relationships;
- autonomous planning;
- autonomous actions;
- background execution;
- task scheduling;
- agent runtime;
- subagents;
- Hermes integration;
- Spatial interface;
- HealthBridge integration;
- new endpoints;
- schema migration;
- new authorization model;
- production identity;
- sessions/device lifecycle;
- synchronization;
- remote access;
- generic workflow engine.

---

## 24. Demo success definition

Sprint 40 succeeds when a first-time supervised participant can use the browser UI to complete this story without manually writing command grammar:

> Save a meaningful fact or project constraint → rediscover it → read it → explicitly create a follow-up item → read the list → restart LUXIOM → confirm that both the knowledge and follow-up remain.

Every actual operation remains explicit, governed, local, inspectable, and user-controlled.

---

## 25. Freeze rule

Once this contract is approved and frozen:

- implementation must conform to it;
- implementation may not expand scope implicitly;
- any material change to authority, storage, backend grammar, endpoint, permission, model policy, or architectural direction requires stopping and reopening the contract/review gate.

Freezing this contract does NOT by itself create code.

Feature implementation becomes authorized only through the separate implementation-authorization gate after contract freeze.
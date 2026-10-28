# Sprint 42 — Governed Local Model-Assisted Intent Preparation v1 — Planning Baseline

Status: PLANNING BASELINE — NOT A FROZEN BEHAVIOR CONTRACT

Reconnaissance: 2026-10-28, America/Tegucigalpa (UTC-06:00).
Authorized scope: Gate 0, controlled investigation, reconnaissance, this single
document, commit/push/planning PR, then HARD STOP for independent review.

SPRINT 42 IMPLEMENTATION IS NOT YET AUTHORIZED BY THIS PLANNING BASELINE

## A. Authoritative Sprint 41 baseline and Gate 0

Initial branch `master`; initial HEAD and fetched origin/master both
`42e66d67248dd11ffceaad534f2462fb85e25d53`. Tracked/staged diffs empty;
initial status exactly `?? tests/unit/reasoning/`. Fetch/prune succeeded.
No local/remote Sprint 42 branch; GitHub returned no open PRs.
Network/auth checks initially failed inside the sandbox; authorized retries
outside it succeeded. No integrity mismatch occurred.

| Immutable tag | Object | Peel | Tree |
|---|---|---|---|
| governed-sprint-41-complete | 7a9f9e91e62b2b2618f3b68a9107fc1b2d0f66b3 | de191a93c710e50509a738747490a38530f6d43a | cc2c2c1637a71d9f949e08eb84e9eb767b917730 |
| governed-sprint-40-complete | 22044ff154287c000251a16e503807151104e81f | 3a3b607d94e359a1410f29da894882424fadb6f6 | 7bf9b8478772c75804b1c378c74f8cc00147e1bd |

Local/remote objects and peels match expected values. Neither tag is moved.
`git tag -v` reported no signature; no signature is claimed or required by this
gate. Integrity is exact object/peel/tree identity.

`LUXIOM_CANONICAL_PROJECT_STATE.md:3-112` records Sprint 41 FORMALLY CLOSED,
reviewed, merged, tagged, backed up/recovery verified and branch cleanup complete.
Contract PR #73 froze Sprint 41; implementation PR #74 released it. Formal closure
PR #76 merged at `a99b760370f4e162927a9423dc6245ce0d7f8c85`.
Frozen contract:
`docs/knowledge-base/SPRINT_41_BOUNDED_NATURAL_LANGUAGE_INTENT_PREPARATION_CONTRACT.md`.
Recorded immutable SHA-256:
`04F2673918F55B382262A6C4C90797A2842ED8C2CC3A9E4447A19E48DB70792C`.
`SPRINT_41_NATIVE_ACCEPTANCE_AND_FINAL_VALIDATION.md`, sections C-E, records 19
native scenarios PASS, 2294 governed tests PASS and 410 real-interpreter parity
vectors. These are historical results, not tests rerun in this planning gate.

Discrepancy: `docs/knowledge-base/02_CURRENT_STATE.md:3-18` still says Sprint 41
planning/not implemented. That section is stale relative to released source and
the canonical release truth above. The canonical file's Sprint 42 not-authorized
statement describes the pre-this-prompt checkpoint. Neither file is modified.
This discrepancy does not invalidate repository integrity or block planning;
canonical synchronization requires a later authorized gate.

## B. Sprint 42 goal

Broader Spanish paraphrases may prepare the SAME FOUR existing intent families
using a LOCAL model only when deterministic recognition cannot recognize an
otherwise eligible request. The model assists interpretation, never execution,
authorization, workspace selection, provenance or permission selection.

## C. Product rationale

Sprint 41's deliberately narrow positive corpus leaves equivalent requests
unrecognized. Bounded extraction can improve that experience while retaining
explicit metadata, editable proposals and governed Send. This is a core capability
behind an architecture-owned contract, not a product-specific reasoning exception.

## D. Foreign-tree investigation and restored custody

The user temporarily relaxed hash-only/no-read custody for this gate only.
Only untracked path found: `tests/unit/reasoning/entities/test_user_request.py`.
Pre-read SHA-256 matched historical:
`45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C`.

| Pre-read metadata | Value |
|---|---|
| Full path | C:\PROYECTOS\JARVIS-OS\tests\unit\reasoning\entities\test_user_request.py |
| Size | 1061 bytes |
| Creation UTC | 2026-09-09 21:25:09 |
| Last-write UTC | 2026-09-10 00:57:36 |
| Attributes | Archive |

`git ls-files --others --exclude-standard` lists the exact path; check-ignore
returns no matching rule. Correction after independent review of PR #78:
path history, object reachability and attributable provenance are distinct.

Remote GitHub tree metadata for commit
`9e5eba78380536353965df6a95721f16e7f19ed8` proves the exact foreign path was an
EMPTY placeholder, blob `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`, size 0.
Local ls-tree agrees, including at `cc6cb8409e879209fabaa1e0cb2c9a5c54d244bb`.
At 9e5eba7 the populated related 49-line test instead occupied
`tests/unit/cognition/reasoning/domain/entities/test_user_request.py`, blob
`1b9b1d973fab9f8e6f465cab682a96f5b865a666`, size 1041 bytes. GitHub commit
metadata and local full-history raw log show
`daa369876e641ae02efc2ef83c47a7ca87eb92f7` REMOVES the empty exact path.
These facts do not establish provenance of the populated untracked contents.

The Gate 0 observation identified the current populated blob as
`85601faa2850695c35a5e47d685963468959c616`. Reconciliation did NOT reopen its
contents or use cat-file -p. `git cat-file -t` confirms blob type;
`git rev-list --all --objects` lists it at the exact path, but BOTH ordinary and
full-history `git log --all --find-object=85601faa...` return NO commits.
Per-ref object reachability and ls-tree identify these eight LOCAL-ONLY refs,
each containing that blob at `tests/unit/reasoning/entities/test_user_request.py`:

| Exact local ref | Tree object (not a commit) |
|---|---|
| refs/codex/turn-diffs/captures/1793217342443/62fc1066-e16a-4e58-9e2c-2cddc2924572/base | a6260cdb159f7b74719e42c566e5810c989474c5 |
| refs/codex/turn-diffs/checkpoints/13d7025dfc49a10cf6c78954d45dbe64/4eac15e9cd085537937cde0ad59fecf1/1792771599714/5a31eefe-0d3a-44ba-9c62-ed585643c159 | 60298164f4c5cf0b89cbd43d4d5cd8f6fa7dfe05 |
| refs/codex/turn-diffs/checkpoints/436cb29138a28255fcd934945b60fff9/4c6074657dbac48adb567c59a3d9e3d5/1792776979870/91737050-bec0-4f8f-ab5e-14e288c39045 | d98969468fbe40c78d64235939eeccefe139b395 |
| refs/codex/turn-diffs/checkpoints/5b7b7385c8c59b1b0f4f123e5e798e69/d7e25df6cc1523f812a1655b60ffb97b/1793216899413/6ecae166-56c7-4360-83f7-1fb4034de24a | a6260cdb159f7b74719e42c566e5810c989474c5 |
| refs/codex/turn-diffs/checkpoints/7624af072acf02a28f07c6ae586e824b/6ee23bf7be5aab90f1eff4f9f122859e/1793032557807/155cae43-233c-4ac4-9090-5542088f9035 | 44ede36e0f0bd76733ef99cbdee35df7e7bbcb20 |
| refs/codex/turn-diffs/checkpoints/cea7a6caa7ee63d31a83e116087cf4fa/6f9c18440adb61ff0cfa36220e5b0ccb/1792772298402/686dd5e9-d8de-4c14-82bb-1ef65585e7d9 | 0976e3408eeee868909fc5bca42b0a695da9b292 |
| refs/codex/turn-diffs/checkpoints/e75608ac16284e88c4e9de0caf932c28/954f272400b6c4d051e3bd99a281dd63/1792770775892/0a71f926-055c-4716-b312-c71ffbfeeec1 | 0976e3408eeee868909fc5bca42b0a695da9b292 |
| refs/codex/turn-diffs/checkpoints/ee5d990c6dd0e41ca31223f26b160a74/4896ae5bbee7957d6037f746f043a185/1793043192558/6f7f281a-de8e-4e23-a42f-c99504fb644c | 0dffea5a51eb883a54575a8766b1b2876808ac1f |

Reachability category: **B. reachable only through local refs not present on
GitHub**, as observed during reconciliation. None of the matching refs points to
a commit; no named branch/tag/commit history containing this blob was identified.
`git ls-remote origin` advertises none of these refs. This is local snapshot
retention evidence only, not proof of authorship, original creation or governed
historical inclusion. No GitHub commit/ref/blob relationship for the populated
foreign path is established. The former exact-historical-blob claim is withdrawn.

The following textual findings are retained ONLY from the authorized Gate 0 read;
no foreign text was read again during this correction.

Controlled plain-text read findings:

- Imports: __future__.annotations, dataclasses.FrozenInstanceError, pytest,
  app.reasoning.entities.user_request.UserRequest.
- No classes; functions/tests: test_should_create_valid_user_request,
  test_should_strip_whitespace, test_should_reject_empty_content (parametrized),
  test_should_be_immutable.
- Referenced symbols include UserRequest, content, request_id, created_at,
  pytest.mark.parametrize, pytest.raises, ValueError, FrozenInstanceError,
  setattr and str. Purpose: creation, trimming, empty rejection and immutability.
- No apparent network/process/filesystem operations, secrets, credentials or
  tokens. Imports, definitions and the pytest decorator would execute upon import;
  no additional top-level I/O/process side effects are apparent. Static inspection
  is not runtime execution or a runtime safety proof.
- Governed `app/reasoning/entities/user_request.py:14-34` still defines the matching
  frozen/slotted entity with UUID/UTC defaults, trimming and nonempty validation.
  This is historical reasoning-domain design still present in master, not the
  active preparation contract; current-state documentation places historical
  app/reasoning outside the active cognitive path.

Corrected classification, exactly one: **E. INSUFFICIENT_EVIDENCE**.
Content is strongly consistent with a legitimate legacy LUXIOM test and its
referenced production entity still exists, but exact attributable provenance of
the populated untracked blob is not established. Remote history proves the exact
path existed only as an empty placeholder in the inspected commits, while a
populated related test existed under a different cognition path. Local-only tree
snapshots retain the populated blob but establish no originating historical
commit or authorship. The current master UserRequest entity was reconfirmed by
read-only governed-source inspection; compatible purpose supports project relevance,
not exact provenance. This supersedes Gate 0 classification A and grants no
authorization to collect/incorporate the file.
No execution, import, module loading, pytest collection, lint, staging, moving,
copying into governed source, modification or deletion occurred.
Post-read SHA-256 equals the pre-read/historical hash exactly:
`45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C`.
Strict custody restored: entire tree stays untracked/unstaged/unchanged, excluded
before collection and from lint. Recommendation: retain pending a separately
authorized historical-test ownership/inclusion decision; no Sprint 42 inclusion
or deletion. No further textual inspection is needed.

## E. Current architecture facts (exact Gate 0 master)

| Fact | Finding and exact source references |
|---|---|
| Browser-local deterministic preparation | Confirmed: app/api/static/local_ui/app.js:54-243 and 1104-1246; index.html:88-150, non-submit Interpret/Reject; styles.css:192-219, hidden/state/focus presentation. |
| Exactly four preparation families | Confirmed: app.js:100-149,184-189,227-235: CAPTURE_KNOWLEDGE, RECALL_KNOWLEDGE, ADD_FOLLOW_UP, READ_FOLLOW_UP. Execution grammar has additional operations; these do not expand preparation. |
| Deterministic execution authority | Confirmed: app/cognition/interpretation/interpreter.py:59-192, closed list/knowledge parser; models.py:16-43,46-78, typed outcomes; routing.py:49-83 interprets before coordinating. |
| Explicit Send boundary | Confirmed: app.js:3008-3066, submit sends exact visible editor without natural-input reinterpretation. |
| Existing request fields | Confirmed: app.js:3030-3035; app/local_command/models.py:320-335; app/api/routes/local_command.py:250-288: proof, requested_workspace_id, text, allow_cognitive_fallback. |
| Fallback post-Send | Confirmed: app/cognition/routing/coordinator.py:22-55 resolves locally then checks explicit fallback authorization before CognitiveProcessor; routing/models.py:33-52 and contracts.py:8-9 define that path. It must NOT serve pre-Send assistance. |
| Runtime reasoning disabled | Confirmed: app/operations/local_interactive_runtime.py:164-165 constructs Settings(REASONING_ENABLED=False, _env_file=None). Preserve it. |
| Generic reasoning abstractions | Confirmed: app/cognition/providers/base_provider.py:9-13 takes CognitiveContext/returns ReasoningResult; ollama_provider.py:10-25 builds reasoning prompt/calls chat. Neither is bounded intent extraction. |
| Ollama HTTP | Confirmed: app/models/ollama_client.py:1-41 uses requests POST model/prompt/stream=false and GET model listing; app/core/config.py:20-23 defaults localhost:11434 /api/generate, /api/tags, llama3.2:3b, timeout 120 seconds. Configurability alone does not guarantee future locality. |

`app/core/container.py:400-548` composes generic reasoning, memory/evidence wrappers
and CognitiveEngine; 550-618 separately composes interpretation/authenticated
routing/gateway. `app/cognition/engine.py:42-72` can retrieve scoped memory and
execute specialist capability plans. Bounded preparation must not call this engine
or inherit those dependencies.
`app/api/interactive.py:15-16,77-101` restricts exact Host and protects ONLY POST
/local/command with Origin/content-type/CSRF. A new route will NOT automatically
inherit path-specific Origin/CSRF protection. Lines 119-139 compose the local app.
`local_command.py:287-288` calls gateway.execute on the execution path.

Reviewed tests: tests/unit/api/test_local_interactive_ui.py:1088-1158 (real
interpreter parity), 1161-1320 (structure/state/harness), 1323 onward (authority/
envelope); tests/unit/cognition/interpretation/test_interpreter.py; browser harnesses
local_bounded_natural_language_intent_preparation.js and
local_bounded_natural_language_intent_ui.js (purity, closed outcomes, guards,
editor/rejection/stale/pending); Sprint 40 guided harness and acceptance evidence.
No tests/harnesses executed during this documentation gate.

## F. Existing Ollama/provider facts

The existing client is synchronous, returns free-form text and has a configured
timeout. It supplies no closed intent schema, strict candidate parser, grounding,
eligibility or authority isolation. Sharing transport may be evaluated; reusing
ReasoningProvider.generate would conflate cognitive reasoning with extraction.
The future adapter requires independent locality, limits and failure containment.

## G. Actual local Ollama environment

Installed: **true**. Executable:
`C:\Users\Lenovo YOGA\AppData\Local\Programs\Ollama\ollama.exe`.
`ollama --version`: **0.40.11** (Get-Command file version is 0.0.0.0).
Service available: **true**, established by successful non-generative ollama list.
Installed model: **llama3.2:3b**, ID **a80c4f17acd5**, displayed size **2.0 GB**,
displayed modified age four months. Candidate Qwen models are absent.
Listing proves inventory, not extraction quality, compatibility or latency.
No generation, install, upgrade, pull/download or machine change occurred.

## H. Actual RAM/environment facts

Read-only Windows CIM: total physical **8,376,537,088 bytes** (about **7.80 GiB**,
8 GB-class); visible memory **8,180,212 KiB**; free at observation **1,404,656 KiB**
(about **1.34 GiB**). Free RAM is transient, not guaranteed headroom. CIM initially
denied inside sandbox, succeeded on authorized read-only retry. Windows PowerShell;
repository C:\PROYECTOS\JARVIS-OS. Sprint 41 evidence records Windows 11 Pro build
26300 historically; that is not a fresh Sprint 42 OS-version observation.

## I. Dependency finding: requests

**requests is NOT directly declared in governed dependency metadata.**
Tracked metadata inventory contains pyproject.toml, whose dependencies are fastapi,
loguru, pydantic, pydantic-settings, uvicorn; dev extras pytest, pytest-cov, ruff,
pyright. No tracked requirements/lock/setup alternative declaring requests found.
OllamaClient imports requests at line 1; installed venv metadata reports
**requests 2.34.2**. It is environmentally available, not a declared dependency;
this does not establish the prior install/transitive chain that supplied it.
Before implementation, freeze direct declaration versus a deliberate declared/
standard-library transport choice. No dependency edits here. This is an
implementation prerequisite, not a documentation-baseline blocker.

## J. Deterministic-first invariant and required proposed flow

Natural text -> Sprint 41 deterministic safety/recognition gate:

1. Prepared -> deterministic result; ZERO model requests.
2. ClarificationRequired -> retain clarification; ZERO model requests.
3. Protected/safety Unsupported -> retain Unsupported; ZERO model requests.
4. Only eligible unrecognized paraphrase with session opt-in -> optional local
   assistance, at most one request per explicit preparation attempt.
5. Closed structured candidate -> deterministic validation -> source grounding
   -> existing deterministic serializer -> visible/editable proposal -> edit/reject
   -> explicit Send -> existing authentication, principal mapping, workspace,
   membership, permission and application gateway path.

No repair prompts/retries, external model/network fallback, auto-Send or authority
downgrade. Model output is data, never executable command authority.

## K. Eligibility and overloaded-reason gap

Only genuine unrecognized paraphrases equivalent to unsupported_request may be
eligible. Never invalid_input, negation, conditional_request, multiple_actions,
context_reference, whole quoted/example requests, ambiguous destination structure,
isolated surrogate, oversize input or already-recognized clarification.

Critical finding: app.js:172-175 maps leading negation/conditional introducers,
quotes/examples to unsupported_request, the SAME reason used for unrecognized text
at line 181. Some conditional/ambiguity checks depend on recognition. A reason
string alone cannot authorize model assistance.
Later contract must distinguish protected rejection from unrecognized eligibility,
freeze conservative safety corpus/precedence and server/browser parity. Enforce
server-side independently; never trust browser eligible=true/reason flags. Uncertain
safety cases remain protected. Existing guards cannot be bypassed.

## L. Closed model-output proposal

Propose a discriminated candidate containing only optional supported/unsupported
outcome, intent and extracted semantic fields. Supported enum EXACTLY:
CAPTURE_KNOWLEDGE, RECALL_KNOWLEDGE, ADD_FOLLOW_UP, READ_FOLLOW_UP.
No fifth intent, tool name, command field/text or authority field.

| Intent | Only proposed model-extractable field names |
|---|---|
| CAPTURE_KNOWLEDGE | value |
| RECALL_KNOWLEDGE | key |
| ADD_FOLLOW_UP | item, list_id (explicitly named list only) |
| READ_FOLLOW_UP | list_id (explicitly named list only) |

Missing fields yield clarification, never hidden commands. Freeze exact discriminator,
missing-field representation and unsupported shape later. Reject unknown/duplicate
keys, wrong types/coercion, unsupported intents, extra/nested fields, alternatives,
multiple candidates and command strings. Parse exactly one bounded JSON object,
no markdown/prose/trailing data. Provider schema/prompt is not the validator.

## M. Source-grounding proposal

Evaluate strict v1: EVERY extracted value must correspond to literal text in the
ORIGINAL input, allowing only contractually defined outer whitespace (propose
existing Python-compatible edge trimming). Preserve case/accents/combining text
and interior whitespace. No normalization, translation, summary or invented strings.
Capture extracts remembered value; Recall requested key/topic for existing exact-key
FIND, not semantic retrieval. ADD extracts one item plus explicitly named list;
READ an explicitly named list.

Substring presence is necessary, not sufficient: deterministically establish the
field's role and explicit destination. A coincidental word in an item, quoted
instruction or 'mis pendientes' is not a list ID. Freeze conservative destination
evidence rules; uncertainty yields clarification/Unsupported, never model authority.

No invented record_id, kind, Capture key, source_type, source_reference, list_id,
workspace, actor, permission, provenance or authority. Capture metadata remains
explicit user controls, not model extraction; any future explicit Capture-key
syntax needs contract review. Generic 'mis pendientes' supplies no default list.
Explicit controls are separate user assertions with validation/conflict checks,
not claimed as model-extracted/source-grounded. Missing metadata stays clarification.
Literal grounding prevents invented strings, not all wrong interpretations; role
validation, adversarial tests and visible review remain necessary.

## N. Failure behavior

| Failure | Safe proposed result |
|---|---|
| Unavailable Ollama/model absent/connection refused | Provider unavailable visibly; no new command; editor retained |
| Timeout/exception/refusal | Sanitized non-command state; bounded wait; no retry/external fallback |
| Malformed JSON/schema invalid/unsupported intent/unknown or duplicate field/extra prose | Reject candidate; Unsupported/non-command |
| Invented/non-grounded/wrong-role field | Reject before serialization; no hidden command |
| Oversize input/response/field/command or isolated surrogate | Reject without truncation/repair |

Retain prior manual editor text marked stale/no new proposal, never accepted new
model output. Provider unavailable is service/UI status, not fifth intent or
execution result; freeze preparation-outcome mapping later. No raw exception/prompt
exposure or persistent input/output logs. Never auto-Send or silently downgrade.

## O. Authority and deterministic command construction

Only existing deterministic builders/serializers create knowledge store :: ...,
knowledge find :: ..., list add ... or list read ... . Knowledge JSON uses exact
existing field sets/escaping; lists retain ID/one-item/delimiter restrictions.
Preserve 8192-code-point command bounds and isolated-surrogate rejection. Any server
builder counterpart requires parity with existing builders and real interpreter,
not a second grammar or execution-parser change.

Candidate is data; deterministic validator is acceptance boundary. No repository,
memory, persistence, gateway, cognitive fallback, auth/permission/workspace decisions
in preparation. Inject no such dependencies; forward no execution proof/workspace
claim. CSRF guards transport, not action authorization. Existing runtime startup
storage/bootstrap remains; zero-access applies to preparation handling/provider
requests, not a false claim startup is I/O-free. No model-selected endpoints,
models, filesystem paths or permissions from input.
Send exact visible editor, no reinterpretation/rebuild; manual edits authoritative.
Denials/revocation still enforced after Send; Prepared grants nothing.

## P. Minimal UI proposal

Retain panel/Interpret, deterministic first. Evaluate explicit session-only
`Allow local model assistance`, default OFF, cleared on refresh, never persisted.
Enabled still means eligible only. Visibly distinguish Deterministic, Local-model
assisted, Clarification required, Unsupported, Provider unavailable; preserve
proposed/stale/edited/pending states, none equivalent to executed authority.
Show literal extracted/missing/invalid fields and validated command in editor.
Preserve Reject/manual edit-back behavior, keyboard/focus/status and Sprint 40
correlation invalidation.
Freeze async cancellation/correlation: input/control/opt-in changes, Reject/manual
editor changes must discard late responses without replacing manual text or
restoring rejected proposals. Block duplicate requests, never queue Send.

## Q. Transport/API alternatives

| Alternative | Evaluation |
|---|---|
| Browser directly to Ollama | Reject: bypasses runtime-owned policy/locality boundary |
| Reuse /local/command or cognitive fallback | Reject: conflates preparation and execution/post-Send authority |
| Distinct local preparation service/endpoint | Recommend: smallest clean non-executing boundary |
| Generic agent/reasoning API | Reject: unnecessary memory/planning/free-form scope |

Exact route UNFROZEN. Prefer browser -> LUXIOM local runtime -> bounded adapter.
Future endpoint must be loopback-only through existing interactive app, Host/Origin
restricted, CSRF protected, strict content type, closed bounded request/response,
finite timeout/concurrency. Explicitly extend path-specific middleware. Verify
loopback binding/provider URL; reject remote URLs, redirect/proxy escapes and
caller endpoints. No persistence, repository access, permission mutation, gateway
execution or cognitive fallback. Readiness never generates/pulls models.

## R. Provider architecture alternatives

| Alternative | Evaluation |
|---|---|
| ReasoningProvider.generate(CognitiveContext) | Reject: free-form reasoning/memory/capability conflation |
| IntentPreparationProvider or equivalent specialized contract | Recommend: architecture-owned bounded extraction, provider/model agnostic data/errors |
| Product/UI-specific Ollama helper | Reject: core functionality becomes product/provider exception |
| Share low-level HTTP only | Conditional on independent limits/locality/schema/failures and declared dependency decision |

## S. Recommended architecture and evaluation candidates

Core bounded preparation service owns closed models, deterministic eligibility,
validation/grounding with specialized injected provider contract. HTTP/Ollama are
adapters. Compose independently in local runtime, preserving REASONING_ENABLED=False
and excluding CognitiveEngine/ReasoningProvider/repositories/gateway. Browser fast
path remains; server independently validates eligibility. Accepted semantic data
reaches deterministic builder/review. Freeze serializer placement/ownership later.

Planning candidate `qwen3.5:2b-q4_K_M`; secondary `qwen3.5:4b-q4_K_M` only with
measured acceptable local memory/performance. No architecture model hardcode.
Small footprint/multilingual structured extraction is evaluation rationale, not
proven local capability. The official [Ollama catalog](https://ollama.com/library/qwen3.5/tags),
consulted 2026-10-28, lists these exact tags at 1.9 GB and 3.3 GB. Download size is
not runtime RAM; only 1.34 GiB free observed, so fit/latency is unproven. Installed
llama3.2:3b is not an automatic substitute/acceptance result. Later authorized native
evaluation must measure peak RAM, bounded context/output, cold/warm latency,
Spanish extraction and failure behavior. No generation/install/download here.

## T. Planned blocks A-E — NOT authorized

| Block | Proposed work/proof |
|---|---|
| A | Closed candidate/proposal models; deterministic validator, eligibility/source grounding; provider-independent tests |
| B | Bounded local adapter; separate preparation service/endpoint; explicit HTTP dependency/locality policy; contained failures |
| C | UI/session opt-in; deterministic-first; provenance/state/async invalidation; manual editor authority |
| D | Security/authority regression; real-interpreter parity; provider failure matrix; zero pre-Send authority proof |
| E | Native Windows acceptance with separately authorized real local model; full governed regression; release lifecycle |

All require later behavior-contract freeze and explicit implementation authorization,
with independent review at governed gates. Model setup/release actions need their
applicable later authorization; this plan authorizes none.

## U. Future test/acceptance strategy

- Model counts: deterministic fast path zero, clarification zero, protected
  Unsupported zero, opt-in off zero, eligible paraphrase at most one. Include
  direct endpoint attempts to bypass browser policy.
- Closed schema/grounding: four families valid/partial; unknown intent/extra or
  duplicate field/wrong type/command text/direct command injection; missing,
  invented, non-grounded, wrong-role, oversize and surrogate fields; malformed JSON,
  refusal, markdown/extra prose. Literal Unicode/limits/interpreter parity.
- Hostile prompt injection and guards: negation/conditions/multiple actions,
  context references, quoted/examples, ambiguous destination, 'mis pendientes';
  substring-present wrong-role fields. No candidate execution/evaluation.
- Timeout/unavailable/absent model/connection refused/exception/refusal matrix;
  bounded sanitized state, no retry/cloud fallback, no new command, editor retained.
- Instrument zero pre-Send repository/memory reads/writes, gateway execution,
  auth/permission/workspace decisions. No execution proof passed to provider.
- Wrong/duplicate Host/Origin/CSRF, type/body/response limits, loopback, redirect/
  proxy policy, concurrency/cancellation. Fake-provider and native evidence separate.
- UI opt-in/reset/provenance, Reject, manual edit/edit-back, stale/late response,
  pending/duplicate-click, keyboard accessibility and literal rendering.
- Exact editor on Send, no reinterpretation/automatic Send; unchanged four-field
  envelope, real interpreter parity; authentication/workspace/membership/permission
  denial and live revocation still enforced after explicit Send.
- Sprint 41 deterministic corpus/harness regression, preserving its pure path
  assertions; separate opt-in-path assertions. Sprint 40 full guided journey.
- Native Windows/browser/model version and measured latency/memory/quality,
  isolated synthetic storage. DOM doubles do not substitute for native acceptance.
- Entire foreign tree excluded BEFORE future pytest collection with
  --ignore=tests/unit/reasoning and before Ruff inspection with
  --extend-exclude tests/unit/reasoning --force-exclude. No foreign import/lint/
  execution/collection. Isolated external temporary/evidence directories.

This gate performs documentation/diff/integrity checks only. No full pytest needed
or run. No proposed tests/native model acceptance claimed complete.

## V. Explicit non-goals

No new intent families, task lifecycle, knowledge edit/delete, planning engine
expansion, agent loops, autonomous execution, auto-Send, semantic/vector retrieval,
persistent conversational memory, implicit workspace/permissions/provenance/list
resolution, default 'mis pendientes' list, external/cloud models/internet fallback,
OpenAI/Anthropic/Gemini integration, mobile/Android/iOS, cloud synchronization,
HealthBridge, Hermes integration, Spatial UI, voice, new business/product billing
or Sprint 43. No canonical state edits, foreign incorporation/deletion, model
installation, implementation, contract freeze or merge in this prompt.

## W. Decisions MUST freeze in later behavior contract

1. Protected-vs-eligible classifier, conservative safety corpus/precedence,
   genuine paraphrase definition, server/browser parity and zero-call rules.
2. Closed candidate/result/discriminator/missing-field/unsupported shapes,
   duplicate/unknown rejection and Provider unavailable outcome/status mapping.
3. Literal grounding/outer whitespace, explicit destination role proof, Capture
   metadata/key limits, explicit-control conflicts and clarification policy.
4. Serializer ownership/placement/shared-builder strategy and parity without
   grammar expansion or trusting model command strings.
5. Specialized provider contract; requests declaration versus deliberate transport
   alternative; configuration owner and loopback/redirect/proxy policy.
6. Exact endpoint/request, no proof/workspace authority, middleware coverage,
   body/field/context/output limits, finite timeout/concurrency/cancellation/errors.
7. Session opt-in/reset/provenance, async stale-response protection, pending/Reject/
   editor authority and Sprint 40 coexistence.
8. Model evaluation/configuration and acceptable memory/latency/quality thresholds;
   separate setup authorization, no architecture hardcode.
9. Block allowlists, test/native/release gates, foreign exclusion and later canonical
   synchronization scope including stale current-state text.

## X. Outcome and hard stop

No integrity/reconnaissance blocker prevents publishing this documentation baseline.
Overloaded reasons, undeclared requests, stale secondary state, absent candidates
and unmeasured model headroom remain explicit future prerequisites, not completed
work. Only tracked change: this document on docs/sprint-42-planning-baseline from
exact master 42e66d67248dd11ffceaad534f2462fb85e25d53. Exact commit/PR subject:
`docs: establish Sprint 42 planning baseline`.
Before commit verify one-file scope, git diff --check, foreign hash and both tags.
No source/test/dependency/canonical truth/machine changes.
After normal push/planning PR: HARD STOP for independent review before merge/freeze.
Do not merge, create contract branch, implement, install/pull model or add/delete
foreign file. This baseline cannot authorize itself.

SPRINT 42 IMPLEMENTATION IS NOT YET AUTHORIZED BY THIS PLANNING BASELINE

# Sprint 41 — Native Acceptance and Final Validation

Status: BLOCK E1 ACCEPTANCE COMPLETE — READY FOR FINAL INDEPENDENT REVIEW

## A. Scope and authority

Blocks A-D independently approved. The user authorized Block E, split into E1 validation and E2 lifecycle work. This evidence records E1 only. Production, existing tests/browser harnesses, the frozen contract and canonical current-state documents were read-only. No tools or dependencies were installed.

Reviewed implementation tip: `47e72a218b6fb7cbaaafb74594392a6a69d0bf11`.
Implementation base: `a0ba052c235b60acd44ad20777fd4251f7bbb3c9`.
Branch: `feat/sprint-41-bounded-natural-language-intent-preparation`.
Pre-E1: 4 ahead / 0 behind; local/remote feature tips matched; master remained at base; no PR. Tracked worktree/index clean, apart from the untracked foreign tree.

Frozen contract: `docs/knowledge-base/SPRINT_41_BOUNDED_NATURAL_LANGUAGE_INTENT_PREPARATION_CONTRACT.md`.
Initial and final SHA-256: `04F2673918F55B382262A6C4C90797A2842ED8C2CC3A9E4447A19E48DB70792C`.

## B. Native environment and isolation

| Property | Observed value |
|---|---|
| Automation | Already-installed Playwright 1.62.1, loaded by Node from the local Codex runtime |
| Browser | Microsoft Edge stable channel `msedge`, version 156.0.4314.42 |
| Executable | `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe` |
| Launch | `chromium.launch({channel:"msedge", headless:false})`; installed browser, headed, real Windows host |
| Windows | Microsoft Windows 11 Pro, 10.0.26300, build 26300, 64-bit |
| Acceptance interval | 2026-10-26 12:52:37-12:52:55 UTC-06:00, America/Tegucigalpa |
| Actual Windows clock sample | 2026-10-26T12:52:39.1149763-06:00 |
| Native flags | `nativeBrowserVerified=true`; `nativeKeyboardVerified=true` |
| Server | Existing LocalInteractiveRuntime + create_local_interactive_app; installed uvicorn, 127.0.0.1:8765 |
| URL | `http://127.0.0.1:8765/local/ui` |

Isolated database: `C:\Users\Lenovo YOGA\Desktop\LUXIOM_ACCEPTANCE\SPRINT_41\20261026-124912\sprint41-native-acceptance.sqlite3`.
New synthetic acceptance data only; no development, prior-sprint or personal database was reused. A generated synthetic acceptance proof was passed transiently to the server and never recorded raw. Request evidence redacts proof. Sends used the delivered CSRF token and normal Host/Origin/CSRF/HTTP/gateway path. Browser fetch was observed, not mocked.

External evidence directory: `C:\Users\Lenovo YOGA\Desktop\LUXIOM_ACCEPTANCE\SPRINT_41\20261026-124912`.
No screenshots/database/profile were added to Git. Playwright used a temporary browser context. External launcher and acceptance script are acceptance-only artifacts.

## C. Native scenarios 1-19

Each PASS includes real browser UI assertions. Deltas count only actual POST /local/command requests; asset GETs are not execution.

| Scenario | Result | Browser-visible evidence / important observed value | POST delta |
|---|---|---|---|
| 1. Capture recognized | PASS | CAPTURE_KNOWLEDGE; literal value | 0 |
| 2. Missing STORE metadata | PASS | Five explicit fields missing; editor unchanged | 0 |
| 3. Explicit STORE completion | PASS | knowledge store :: {"record_id":"s41-native-record","kind":"fact","key":"MedSupply","value":"MedSupply entrega los martes.","source_type":"manual","source_reference":"native:s41"} | 0 |
| 4. Exact-key Recall | PASS | knowledge find :: {"key":"MedSupply"} | 0 |
| 5. Explicit list ADD | PASS | list add tareas-native :: llamar a MedSupply | 0 |
| 6. Generic ADD clarification | PASS | list_id missing; no default | 0 |
| 7. Explicit list READ | PASS | list read tareas-native | 0 |
| 8. Generic READ clarification | PASS | list_id missing; editor retained | 0 |
| 9. Unsupported request | PASS | unsupported; editor retained | 0 |
| 10. Negation | PASS | No Capture; no command | 0 |
| 11. Hostile literal payload | PASS | Literal text/JSON; no script element or dialog | 0 |
| 12. Natural input stale and explicit reprepare | PASS | Old command retained while stale; explicit reprepare clears stale | 0 |
| 13. Manual editor authority on real Send | PASS | Actual POST text exactly list read tareas-native; no reinterpretation | 1 |
| 14. Interpret zero-request matrix | PASS | Prepared, clarification, unsupported and stale/reprepare add zero POSTs | 0 |
| 15. Fresh Prepared governed Send | PASS | One real HTTP 200; exact editor and unchanged four-field envelope | 1 |
| 16. Wrong proof and live permission denial | PASS | wrongProof: HTTP 403 access_denied; liveRevocation: HTTP 403 local_permission_denied; same running runtime; no projection | 2 |
| 17. Native Sprint 40 Capture / Recall / Follow-up / Verify | PASS | All four stages completed from five real governed Sends | 5 |
| 18. Native keyboard navigation, focus and status | PASS | Tab reached input/Interpret/Reject; Enter prepared; Space rejected; focus-visible and status verified | 0 |
| 19. Reject four paths including keyboard and edit-back | PASS | Untouched cleared; manual/edit-back retained; clarification/unsupported retained unrelated editor; no restoration | 0 |

Scenario 16B ran after 17-19 so revocation could not interrupt the guided journey. Row 16 aggregates wrong-proof and live-revocation requests. The same server stayed running during revocation.

Overall: all 19 scenarios PASS. Hostile payload created no injected script element and zero dialogs; its exact value remained JSON string data. Manual Send transmitted `list read tareas-native` exactly, without preparer invocation during Send. Fresh Send transmitted the exact visible STORE through the unchanged four-field envelope: proof, requested_workspace_id, text, allow_cognitive_fallback.

Wrong proof: actual HTTP 403 / `access_denied`, normal Failed Result.
Live revocation: actual HTTP 403 / `local_permission_denied`, no projection or visible list data, after revoking LIST_ITEMS_READ through SQLitePermissionGrantRepository on the same live database without restarting the server.

Sprint 40: Capture STORE -> Recall FIND -> selected READ -> Follow-up ADD -> Verify READ; five separate real Sends, four visibly completed stages. Separate synthetic guide IDs/list IDs avoided collisions.

Keyboard: actual Tab navigation reached the textarea, Interpret and Reject; Enter activated Interpret, Space and Enter activated Reject. Verified :focus-visible, non-none computed outline, Reject accessible button name and changing role=status content. This records browser focus/status semantics, not screen-reader audio.

Reject: untouched Prepared cleared only its generated editor; manual and edit-back-to-original Prepared retained current text; ClarificationRequired/Unsupported retained unrelated manual commands. Each path dismissed state without POST or hidden restoration and preserved natural input.

## D. Native counters and cleanup

| Counter | Measured value |
|---|---|
| Interpret actions | 27 |
| Reject actions | 9 |
| Stale invalidation input events with an active result | 33 |
| Explicit Sends | 9 |
| Actual command POSTs | 9 |
| Interpret POST delta | 0 |
| Reject POST delta | 0 |
| Invalidation POST delta | 0 |

Actual preparer calls: 27, equal to explicit Interpret activations. Per-action zero-POST assertions and browser network observation back preparation/rejection/invalidation claims.
Cleanup PASS: browser closed; stdin-triggered graceful uvicorn shutdown; runtime exited; port 8765 no longer listened. Separate Windows TCP listener check returned no listener. No acceptance background process remains.

## E. Full governed automated regression

Native acceptance and cleanup passed before full regression began.

Full pytest, using project venv and DEBUG=false only in process:

```powershell
.venv/Scripts/python.exe -m pytest --ignore=tests/unit/reasoning -q -p no:cacheprovider --basetemp 'C:\Users\Lenovo YOGA\AppData\Local\Temp\luxiom-sprint41-e1-full-20261026-1254' --tb=short
```

Exit 0: **2294 passed, 0 failed, 0 skipped, 0 xfailed**, 52.67 seconds. The entire `tests/unit/reasoning/` tree was excluded before collection with --ignore; it was not tested. Temp files stayed in the isolated external basetemp.

Global Ruff:

```powershell
.venv/Scripts/python.exe -m ruff check --no-cache app tests --extend-exclude tests/unit/reasoning --force-exclude
```

Exit 0, All checks passed. Foreign tree excluded before inspection.

| Unchanged Node harness | Checks | Categories | Evidence |
|---|---|---|---|
| `tests/browser/local_bounded_natural_language_intent_preparation.js` | 6045 | 36 | PASS; actualRequests=0; vectors=410; forbiddenAccesses=0 |
| `tests/browser/local_bounded_natural_language_intent_ui.js` | 912 | 72 | PASS; actualRequests=0; forbiddenAccesses=0; preparationInvalidationRequests=0; mockedFetchCalls=5; explicitSubmissions=6 |
| `tests/browser/local_knowledge_command_assistance.js` | 406 | not emitted | PASS; actualRequests=0; vectors=15 |
| `tests/browser/local_knowledge_browse.js` | 66 | 13 | PASS; actualRequests=0; vectors=7 |
| `tests/browser/local_knowledge_browse_after.js` | 141 | 17 | PASS; actualRequests=0; vectors=45 |
| `tests/browser/local_guided_capture_recall_action.js` | 14 | 6 | PASS; actualRequests=0 |
| `tests/browser/local_guided_capture_recall_action.js --capture-recall` | 24 | 15 | PASS; actualRequests=7; vectors=3 |
| `tests/browser/local_guided_capture_recall_action.js --follow-up` | 134 | 30 | PASS; actualRequests=0; vectors=27 |
| `tests/browser/local_guided_capture_recall_action.js --verify` | 199 | 29 | PASS; actualRequests=0; vectors=26 |

Block A retained 410 Prepared vectors with real Python interpreter parity through the full UI pytest test. DOM-double native flags remain false and are separate from native E1 flags. The capture-recall harness emits its established request counter; it is not an external-network claim for Node tests.

JavaScript: node --check passed for app.js and every tracked tests/browser/*.js: seven files, zero failures.
Pyright not executed: it is declared/configured as a development tool, but no current Sprint 41 mandatory Pyright lifecycle gate was found. The historical Sprint 31 checklist does not establish an E1 requirement. No new optional gate/tool introduced.

## F. Cumulative implementation self-review

Codex self-review, not the required independent review. Complete cumulative implementation/test diff reviewed.
Working-tree/index diff checks and `git diff origin/master...HEAD --check` PASS. Tracked worktree/index remained clean before this evidence document.
Exactly eight cumulative implementation/test files; 2058 insertions:

- `app/api/static/local_ui/app.js`
- `app/api/static/local_ui/index.html`
- `app/api/static/local_ui/styles.css`
- `tests/browser/local_bounded_natural_language_intent_preparation.js`
- `tests/browser/local_bounded_natural_language_intent_ui.js`
- `tests/integration/api/test_local_command_route.py`
- `tests/unit/api/test_local_interactive_ui.py`
- `tests/unit/local_command/test_gateway.py`

Findings: no backend production, schema, migrations, permission implementation, provider/model enablement or external dependency changes. No hidden Send, semantic retrieval, inferred provenance, default list, automatic workspace authority, Sprint 42 work or foreign file. Preparation remains pure; execution uses existing explicit governed Send. No product defect requiring correction found.

## G. Custody

Foreign exact file: `tests/unit/reasoning/entities/test_user_request.py`.
Initial/final SHA-256: `45CF806561DB59828555A0A14DB7C5106B309F3F0B2122C68E5F0C37FBD3C49C`.
Only Get-FileHash accessed that exact file; no open, search, import, execution, collection, lint, modification, staging or copying into evidence.

Frozen contract initial/final SHA-256: `04F2673918F55B382262A6C4C90797A2842ED8C2CC3A9E4447A19E48DB70792C`.

Sprint 40 tag `governed-sprint-40-complete`: type tag; object `22044ff154287c000251a16e503807151104e81f`; peel `3a3b607d94e359a1410f29da894882424fadb6f6`; tree `7bf9b8478772c75804b1c378c74f8cc00147e1bd`. No movement or history rewrite.

## H. External evidence SHA-256 manifest

Retained files hashed after shutdown and regression. Screenshots supplement assertions. Database is synthetic, not a release backup.

| File relative to external evidence directory | SHA-256 |
|---|---|
| `acceptance_server.py` | `413A2F070139B241F9C37944F536F927047CA8936066AFFF133CBAE8CE2D3A4E` |
| `capture-clarification.png` | `9E7A27B61364387BD21F120EB8970489A927C665AFC7CFDB076015D047240FCD` |
| `full_pytest.log` | `1F2D920C8B8592B2227A0BFF1D52978320F08EEC722F57D09D694A9F334BB489` |
| `global_ruff.log` | `AF352A86840AD0AF3D37EA0D9197F868363A6DAC6B1C2EF5D2722F6B41D2D9AF` |
| `guided-complete.png` | `246BD6A77F58C3E43DF67FC5B07393AC8F761D8C7D11650971B92CF49CCEB5E8` |
| `hostile-literal.png` | `7A1DCA774A9FE6E2D446AEE542E7E317C5435201AFAE7964DF23EEEBC5AE811A` |
| `keyboard-reject-focus.png` | `9B5E9BE0F1C5735F747BF0A916C7E8F101FA3D1BF77FF0588735418FC99A3BDA` |
| `live-permission-denial.png` | `CE8C7D30D389DAD15B2D0E7CCC3E792A3F759AF8F454F367D4CE69E7BE1A5A54` |
| `native_acceptance.cjs` | `BDE6065A23BF0F62D6603D9B3152A16AA442DA11B452DD0EFD7A0CECBDD90299` |
| `native_acceptance.json` | `F6CDD47624115EA374CDF2A76021DFCCF0CC2431A1FC6646E4EFF07B37515D14` |
| `native_acceptance.log` | `48EDB98C8077CF680516157053B376905FF9B1706E27984693680217BAE4C1B2` |
| `node_regression.json` | `06D2735498B7E60A9C2FE7472AD472FAADA3AEB7168E18F1E68A0EFDC732631A` |
| `prepared-store.png` | `EBF0CBE0BEB4FE7CB44BB5E43B7AD176095E851136BA4AB4A5F76C41E9130949` |
| `server.log` | `225EED7CF7AABADF9CC2801F65FC3E35752A140EBA55C9463D1736F46D3133A7` |
| `sprint41-native-acceptance.sqlite3` | `BF23C0AC5084FA69E8BB1DDCBCE4D2385839AF98B9E693D2ED2E7C890CA4D3E7` |
| `stale-input.png` | `DBEBB3DE219960B19BD36DB6D449989CD9D3C75E130F67851E96099585D057F9` |

## I. Hard stop and exact next gate

NO PR / NO MERGE / NO TAG / NO RELEASE BACKUP YET

Implementation remains unmerged and published for independent review. No release-truth update, formal closure or feature-branch deletion. Only this new tracked evidence document is authorized in E1.

Exact next gate: **FINAL INDEPENDENT REVIEW OF E1 BEFORE IMPLEMENTATION PR**.
E2 remains authorized as part of Block E but must not begin until that review passes.

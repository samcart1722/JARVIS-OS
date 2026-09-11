# Luxiom — Start Here

## Current checkpoint - Sprint 38

Implementation `b690e299ac4737f7323fdaf631c459f5f25ce80b`, PR #58,
ordinary two-parent release merge `97e2bc0ba51e4bb571b9ee03f72f4c0d394c70c4`.
Parents, in order: `e26b8a6c7b89132b9ff2221b1bc35d0726cba236` and
`b690e299ac4737f7323fdaf631c459f5f25ce80b`.
Release tree `683ee3336b17ec4d63f5b542e1553ddb9e2fb445` equals the approved
feature tree; exactly 36 authorized files changed from the first parent.
Annotated tag `governed-sprint-38-complete`, object
`70e48c1d4ccb813b064136507d44e90c71d752b3`, peels to that release merge.
Exact annotation: `Sprint 38 - Authorized local knowledge browse v1`.

Authorized local knowledge browse v1 adds explicit `knowledge browse :: {}`
through the existing authenticated local command flow. The separate
`knowledge.records.browse` permission precedes a workspace-scoped metadata
lookup. At most 50 summaries expose exactly `record_id`, `kind` and `key`,
with `truncated` derived from a bounded 51st-row lookahead. No value,
provenance, workspace, total or cursor is exposed in the BROWSE projection.
Prepare BROWSE and selection-based Prepare READ only write the editor;
explicit Send submits its exact text. A separate READ rechecks authorization.
STORE/READ/FIND, lists, provenance requirements, local-first terminal behavior,
identity boundaries and SQLite schema v4 remain preserved.

Post-merge validation observed by Codex: 1946 PASS / 0 FAIL / 0 SKIP; global
Ruff and diff checks passed. Native acceptance PASS (14 scenarios) is reported
by the operator, not personally observed by Codex. See
[canonical evidence](LUXIOM_CANONICAL_PROJECT_STATE.md).

Implementation and tag are complete.
The prepared documentation synchronization was committed as
`6e888c973237350fb8e8d9d449c131ff038205d6` on
`docs/sprint-38-release-truth`, published to origin, with documentation PR #59
open. Independent review of PR #59 was executed and remains BLOCKED solely by
stale statements about documentation commit/publication/PR status. Corrective
documentation synchronization is in progress; PR #59 is not yet approved.
Documentation merge and formal Sprint 38 closure remain pending. Sprint 39 is
NOT STARTED and NOT AUTHORIZED.
No verified Sprint 38 backup is recorded; see
[recovery status](docs/knowledge-base/08_BACKUP_AND_RECOVERY.md).
Sprint 39 is NOT STARTED, with no selected scope or authorization.

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Historical checkpoint - Sprint 37

At that checkpoint, Sprint 37 - Local Knowledge Command Assistance was the latest governed
implementation release. PR #56 merged at
`4dfaff1afdd11ab1258a52671e6799a3a442d16d`, tree
`cb220d0661708af226ffa8faefc5c00bba0fda4c`, tagged
`governed-sprint-37-complete` (object
`1f5863ef15759829e1fbd06c97deb5a6496ff1e6`, peeling to that merge).
It adds explicit local STORE/READ/FIND command preparation, an authoritative
editable command, strict serialization and validation, and submission guards.
Backend authority, fallback and result projections remain unchanged.

Post-merge `1645 passed in 28.10s`, Ruff and diff success are previously
approved, user-reported evidence. Reviewer Node/ASGI results and manual Edge
acceptance have separate provenance; none establishes universal zero network
traffic or CI approval. The implementation backup is verified and its branch
was cleaned locally/remotely. See [canonical evidence](LUXIOM_CANONICAL_PROJECT_STATE.md)
and [backup hashes](docs/knowledge-base/08_BACKUP_AND_RECOVERY.md).

This is later release-truth documentation. It does not move the immutable
implementation tag or require another implementation backup. At that checkpoint, Sprint 38 had no
selected scope or authorized implementation; planning remained separate.

## Historical checkpoint - Sprint 36

At its release checkpoint, Sprint 36 was the latest formally closed governed
implementation release.
It adds structured local knowledge result projections for STORE, READ and
FIND through the existing application gateway, HTTP mapping and minimal UI.
Canonical text remains authoritative; projections do not establish authority.

Implementation release: PR #54, merge
`b3e5516e70616d8a5a0b30d5e0f01d07af9b7787`, tree
`e657dcf565b5600b2b26d71aea7e49bc67799168`.
Immutable tag: `governed-sprint-36-complete`, annotated object
`16e1b3ad9f1239c86e2786d81722620fa1b7c289`, peeling to that merge.
The separate documentation PR #55 merged at
`30b724a287c58ac881ddaab202f9b5f0778e1af9`.

Recorded Sprint 36 validation: 1643 passed / 0 failed.
Verified backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260902_110324_SPRINT36`.
These are historical release results, not new executions by this correction.
Later documentation changes do not move the immutable release tag.

## Historical checkpoint - Sprint 35

Sprint 35 — Structured Local List Result Projection v1 was the governed
implementation release at that historical checkpoint.

Release identity: implementation `fd6ecb3a07c9b640892df40561006d79f531c622`,
PR #52, merge `c2dbab846cc7116568f59786233b64c0f01ab038`, tree
`c65d2bed9158e2630c0912e398bc09eb30a5405e`, tag
`governed-sprint-35-complete`, object
`bae5bcc128d9df1e539952ff3e63183d31aeb6f9`. Successful authorized local list
results now pass from the typed intent through a closed application ADD/READ
projection, dedicated HTTP projection, and safe minimal UI rendering. Canonical
text remains authoritative; authentication, membership, permission, loopback
security, SQLite, local-first routing, and fallback behavior remain unchanged.
No generic/knowledge projection or Core, Hermes, or Spatial work was added.

Validation: 1,535 repository tests, Ruff, `compileall`, release diff check,
post-merge operational proof, and manual browser acceptance passed. Backup:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260828_131542_SPRINT35`. This later docs
sync may advance `master` but cannot move the immutable tag, create another
Sprint 35 implementation tag/backup, or authorize Sprint 36.

## Historical checkpoint — Sprint 34

Sprint 34 — Local Interactive Runtime & Minimal UI Foundation v1 was released
through PR #50 at merge `adbd17d564962c6d22617b5857aaaec7da051b08`, tree
`a82e5c4c56b9fdb8660ef0fd878ea89364514b54`, under immutable tag
`governed-sprint-34-complete`. At that checkpoint the public UI exposed
canonical text without structured list projection; its 1,433-test validation
and governed release evidence remain historical truth.

## Historical checkpoint — Sprint 33

Frozen baseline and implementation commit:
`f1e1519eedd6f021cb98c6ac8a9242f6b946b645` and
`9f4b86beddaa1e2550e054a55e6c743c87f2723c`

PR #48 merged through ordinary two-parent merge commit:
`9af9984691b034710243e1da487767108915ce3a`

Release tree: `3a1317dc1a1c295ae5e2b77947a149cf138134ba`

Immutable governed tag: `governed-sprint-33-complete`

Annotated tag object: `4d0774ee5172da9eff0ee246011775980aac367f`

The tag peels to the merge checkpoint above. Later documentation commits may
advance `master` without moving that immutable tag.

Post-merge validation passed 134 architecture tests and 1,293 repository tests.
Ruff, `compileall`, and `git diff --check` passed. GitHub reported no CI/status
checks; this is not a claim that CI passed.

The authoritative recoverable backup is:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260826_122727`

Complete bundle, source ZIP, and backup-manifest SHA-256 values are:
`E3CEE9B8156248D3627872D3558DBB56B923BD791E2B9FDE2EB951CBFC8AB7E4`,
`BB18BDF291BD9DB02C2F19B8AF886187A750A65EDBC98CB0926DC46F68D49576`, and
`E92D45BA2EA7CB8E8D20C226343308AC55887E1E9FE40F0D726A45550BAF3803`.
Backup verification passed.

Sprint 33 preserves `PermissionGrantRepository` as exact lookup/create and adds
a separate `PermissionGrantRevocationRepository` with exactly `revoke`.
Revocation performs exact, case-sensitive physical removal of the current
actor/workspace/action grant. Present and absent revocations both return `None`;
re-grant remains possible. Schema version remains 4, and no audit history,
soft delete, expiry, RBAC, Container management, or public revoke endpoint was
added. Authentication, mapping, membership, and action authorization remain
separate.

The operational proof uses separate `revoke` and `verify` Python processes
against the same external SQLite database. The second process opens fresh
storage and proves the exact grant remains absent and authorization denied.

The feature branch was cleaned locally and remotely after merge, validation,
tag verification, and backup. Sprint 33 is formally governance-closed at
`9af9984691b034710243e1da487767108915ce3a`. This later documentation patch
reports that already-established closure; it is not part of or a movement of
the immutable release.
No subsequent implementation sprint is authorized merely by this checkpoint.

Sprint 25 is completed through merged PR #24 at
`1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`
(annotated tag object `6e0de87b426e4a7d4c3103bdffc77f2b171aa30f`). It adds
strict JSON `knowledge read` / `knowledge store` commands to the existing
interpreter and text router. This is deterministic structured-command parsing,
not general natural-language understanding. Malformed commands in the
`knowledge` namespace are terminal; public HTTP remains unchanged.
Release validation passed 680 tests, including 85 focused tests. Sprint 26 was
subsequently implemented and merged as described above.

Sprint 23's explicit application coordinator tries an already-typed local
intent first. Handled local success or failure is terminal; only
`not_handled`, explicit fallback authorization, and valid cognitive input can
select the existing cognitive path.

Before Sprint 32, the coordinator/local-first command path was not exposed
through HTTP. Sprint 32 now exposes the governed authenticated local-command
path through the LOCAL-USE `POST /local/command` endpoint. That endpoint reaches
`LocalCommandTextRouter`, deterministic interpretation,
`LocalFirstCognitiveCoordinator`, and the governed downstream local capability
path only after authentication, principal-to-actor mapping, workspace selection,
and membership admission. The coordinator itself performs no general
natural-language parsing, and cognitive fallback remains explicit and is never
automatic. The historical `/brain/think` `CognitiveEngine` route and legacy
`/knowledge` remain separate. Default `Container` construction remains
in-memory and inert.

- The current runtime extends the released Sprint 22 durable local foundation
  with explicit, caller-authorized routing coordination.
- The historical Sprint 32 immutable governed implementation release tag is
  `governed-sprint-32-complete`; its annotated tag object is
  `c1f4267177d316d303c8c4c0e7fd3728afdcad32` and it peels to
  `08c15e3ee225c4cdb2f382af5464da01d33d3f6d`.
- The historical `/brain/think` path remains a `CognitiveEngine` route: input
  becomes a `Goal` and `CognitiveContext`, is classified,
  routed to a specialist, converted to a `Plan`, traversed by
  `CapabilityExecutor`, and formatted by `ResponseStage`.
- Sprint 21 originally introduced a typed, authorized, deterministic local list
  path with zero model calls and without HTTP exposure. Sprint 32 later exposes
  the governed authenticated local-command chain through the LOCAL-USE
  `POST /local/command` endpoint. There is no automatic natural-language routing
  or resolve-or-reason bridge.
  Classification within the historical path still falls back
  to `Domain.UNKNOWN`. The public `CognitiveEngine` path uses
  `CapabilityExecutor` and registered concrete capabilities; its default policy
  selects `NormalizedInputCapability` unless reasoning is explicitly enabled.
  `/brain/think` supplies no explicit scope and therefore does not use the
  separate Sprint 21 local resolver. Sprint 32 separately exposes the bounded
  local-use `POST /local/command` authenticated local-command surface.

## Essential guardrails

The model is not the Core. The Core remains domain-independent. Specialists
plan; reusable capabilities perform work; the `CognitiveEngine` orchestrates;
the `Container` composes dependencies. Runtime and architecture documentation
must remain aligned. Record material architectural changes through an ADR.

Do not change architecture before reviewing the Product North Star, Cognitive
Lifecycle, and applicable ADRs. At this checkpoint no ADR records directory or
approved ADR was found; do not treat draft standards or RFCs as decisions.

## Required reading order

1. [Canonical Project State](LUXIOM_CANONICAL_PROJECT_STATE.md)
2. [Product North Star](docs/00_Product_North_Star.md)
3. [Cognitive Lifecycle](docs/01_Cognitive_Lifecycle.md)
4. [Local-First Knowledge and Model Policy](docs/02_Local_First_Knowledge_and_Model_Policy.md)
5. [Knowledge Base index](docs/knowledge-base/00_INDEX.md)
6. [Current State](docs/knowledge-base/02_CURRENT_STATE.md)
7. [Runtime Architecture](docs/knowledge-base/03_RUNTIME_ARCHITECTURE.md)
8. [Decisions and Guardrails](docs/knowledge-base/04_DECISIONS_AND_GUARDRAILS.md)
9. [Technical Debt](docs/knowledge-base/05_TECHNICAL_DEBT.md)
10. [AI Handoff](docs/knowledge-base/07_AI_HANDOFF.md)

The complete recovery documentation lives in
[`docs/knowledge-base/`](docs/knowledge-base/00_INDEX.md).

## Minimum verified commands

Run from the repository root in Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest
git status --short --branch
git log --oneline --decorate -10
```

The project metadata requires Python 3.12 or newer and declares development
dependencies in `pyproject.toml`. If the existing virtual environment is
unavailable, create and install one explicitly:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

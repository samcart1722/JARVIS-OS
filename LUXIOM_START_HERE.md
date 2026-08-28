# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint — Sprint 35

Sprint 35 — Structured Local List Result Projection v1 is the latest governed
implementation release; Sprint 34 and earlier releases remain historical.

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
- The latest immutable governed implementation release tag is
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

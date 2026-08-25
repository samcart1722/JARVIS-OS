# Luxiom — Start Here

Luxiom is a Cognitive Operating System: a domain-independent cognitive core
intended to support multiple products through reusable specialists,
capabilities, and replaceable tools/providers. HealthBridge is the first
planned consumer. Luxiom is not a chatbot, an LLM wrapper, a conventional
agent, or a product tied to one industry.

## Current checkpoint

Sprint 32 — Authenticated Local Command Application Gateway v1 is the latest
governed implementation release.

Frozen base and implementation commit:
`7aa29bdc894fe646d9e76cb0466d2e26fd44bc88` and
`a56a11f1b92b08df5e310aea749d9cda07570b65`

PR #45 merged through ordinary two-parent merge commit:
`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`

Release tree: `d9e31be190d8077886ce6f85642f9b89d1fd8529`

Immutable governed tag: `governed-sprint-32-complete`

Annotated tag object: `c1f4267177d316d303c8c4c0e7fd3728afdcad32`

The tag peels to the merge checkpoint above. Later documentation commits may
advance `master` without moving that immutable tag.

Post-merge validation passed 129 architecture tests and 1,273 repository tests.
Ruff and `compileall app tests` passed.

The authoritative recoverable backup is:
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260825_103049`

Complete bundle, source ZIP, and backup-manifest SHA-256 values are:
`F1A1CC107C9D2864E767F03BFECB19EE4BE3D03C4061535FBDF30F66B268A07B`,
`D6F91E1E9B66064CB3928A08D0D8F8B115B69632D20D66C85F77291608868B2F`, and
`46F4612172505B5AAAC93AEB58CBFF0411C5BB038DBBCC352F122AFA1FAE37CA`.
Backup verification passed.

Sprint 32 adds a framework-independent `app/local_command` boundary and a
bounded local-use `POST /local/command` development surface. The dependency
direction is `app/api` → `app/local_command` →
`AuthenticatedLocalCommandRoutingService` → the existing governed downstream
chain. Its closed application contracts require strict explicit cognitive
fallback, secret-aware proof handling, pickle rejection, and fixed sanitized
unexpected-error responses.

The historical `/brain/think` endpoint remains the separate `CognitiveEngine`
route, and legacy `/knowledge` remains separate. Sprint 32 does not make either
route authenticated. It adds no production authentication, durable credentials,
JWT/OAuth, sessions, devices, RBAC, administration, public Internet exposure,
CORS, UI, runtime SQLite credential composition, or automatic fallback.

The first independent implementation review found two HIGH issues: proof was
pickle-serializable and the initial manifest hash semantics were incorrect.
Both were corrected and explicitly closed by the approving second review. The
staged-index attestation and final pre-merge review also approved the exact
release. Approved worktree and committed snapshot SHA-256 values are
`47A5B64330FB2DE1502CD32D77593E2389ECF594D1187560FDA08DF15E552A33` and
`2F28B3527701E73986A14331E4763629EDB439EF4A1B5E958FD125EB1F4CAE7E`;
manifest v2 and staged manifest v3 SHA-256 values are
`97F4E58613511999429D114483821EC110A35C6EACD0F2A4DF8359CE3C59D28C` and
`2ACA626A456D9A8989268C7796D693DFC0654C00A2E08F9D14A7752490FB1043`.

The feature branch was cleaned locally and remotely after merge, validation,
tag verification, and backup. Sprint 32 is formally governance-closed at
`08c15e3ee225c4cdb2f382af5464da01d33d3f6d`. This later documentation patch
reports that already-established closure; it does not establish or move it.
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

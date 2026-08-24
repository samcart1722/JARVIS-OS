# AI Handoff

## Recovery brief

1. **Identity:** Luxiom is a domain-independent Cognitive Operating System.
   HealthBridge is a product/client, not part of the Core.

2. **Canonical branch:** `master`.

3. **Latest governed implementation release:** Sprint 31 — Durable Action
   Permission Foundation v1.

4. **Release commit:**
   `9cad78ed22f0a6aef26eda0623d0f544cf65e5be`

5. **Release tree:**
   `5ad6dc854c546e82cdab6c6fd5a5c48072b7fc0d`

6. **Governed tag:** `governed-sprint-31-complete`

7. **Annotated tag object:**
   `2f52c2973bd349bd4302d7bb1e59307f5b14708c`

8. **Validation:** 117/117 architecture tests and 1119/1119 repository tests
   passed. Ruff and `git diff --check` passed.

9. **Authoritative recoverable backup:**
   `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260821_095503`

10. **Architecture boundary:** authentication, principal-to-actor mapping,
    workspace selection, membership admission, and action authorization remain
    separate. Membership does not imply permission.

11. **Sprint 31 permission semantics:** durable grants match the exact
    `(ActorIdentity, WorkspaceIdentity, Action)` triple. Absence of a grant
    denies access. Known repository failures fail closed.

12. **Composition:** default `Container` remains no-I/O. Durable permission
    storage exists only through explicit repository injection.

13. **Not added by Sprint 31:** roles/RBAC, groups, inheritance, wildcards,
    explicit deny rules, public grant/revoke APIs, production authentication
    transport, credential persistence, JWT/OAuth, sessions, device lifecycle,
    remote identity providers, or cloud synchronization.

14. **Review truth:** independent review was unavailable for Sprint 31 and no
    independent review is claimed. Same-assistant technical and adversarial
    reviews were performed; one schema-verification defect was found and
    corrected before release.

15. **Governance state:** implementation merge, immutable release tagging,
    backup verification, and bundle recovery are complete. Release-truth commit
    `d79552f9ab19d7b2da9f2a60be4ef48b8b9608cd` merged through PR #41 at canonical
    merge `7f73ffe1686cb069e3b1ec93283ffda9cdd485ca`; canonical validation passed 117
    architecture and 1,119 repository tests, Ruff, and `git diff --check`. The
    merged implementation and release-truth branches were cleaned locally and
    remotely. PR #42 merged through ordinary two-parent merge commit
    `fa90defc44ad756a33f11e470105db57a440e201`; final canonical validation passed,
    the closure working branch was cleaned locally and remotely, and final
    governance verification confirmed the closure conditions. Sprint 31 is
    formally governance-closed at that canonical checkpoint. This post-closure
    documentation record reports, rather than establishes, that state.

16. **Next implementation:** no Sprint 32 implementation is authorized.
    Any next sprint remains an unfrozen planning and contract-definition
    boundary until explicitly approved.

## Required recovery order

1. Read `LUXIOM_CANONICAL_PROJECT_STATE.md`.
2. Read `LUXIOM_START_HERE.md`.
3. Verify Git branch, HEAD, `origin/master`, tag object, tag peel, and worktree.
4. Read Product North Star and Cognitive Lifecycle.
5. Read Current State, Runtime Architecture, Decisions and Guardrails,
   Technical Debt, and Roadmap.
6. Run the configured architecture and repository test suites.
7. Compare documentation against executable runtime before proposing changes.

## Non-negotiable guardrails

- The model is not the Core.
- The Core remains domain-independent and infrastructure-independent.
- Local deterministic capability is preferred when sufficient.
- Memory and knowledge belong to Luxiom, not to a model.
- Identity, workspace, membership, and action authorization remain explicit
  and separate.
- Public transport does not silently acquire internal capabilities.
- Do not infer architecture or release truth from old sprint-number collisions.
- Do not move, recreate, delete, or retarget immutable governed release tags.

## Resume instruction

Resume from canonical `master` at
`fa90defc44ad756a33f11e470105db57a440e201`, not from historical recovery text.
Sprint 31 implementation, release-truth integration, closure-truth integration,
final validation, governed working-branch cleanup, and formal governance
closure are complete. This post-closure documentation record does not establish
or condition that closure. Do not begin a subsequent implementation sprint
without explicit authorization; Sprint 32 scope remains unfrozen.

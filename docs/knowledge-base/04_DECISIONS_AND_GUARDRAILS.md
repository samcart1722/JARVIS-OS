# Decisions and Guardrails

No approved ADR records were found in the repository. The ADR standard itself
is a draft and `docs/adr/` does not exist. The following consolidation therefore
preserves the status and source of each statement rather than inventing ADRs.

## Sprint 27 released guardrails

- A binding key is an opaque configured lookup selector, not authentication,
  a credential, token, API key, or identity proof.
- `ActorIdentity` and `WorkspaceIdentity` are typed values, not proof of
  identity or access. A configured binding is process state, not durable
  account or workspace membership.
- Workspace selection is explicit; there is no default. Trust resolution
  precedes routing and remains distinct from downstream `PermissionPolicy`
  authorization.
- Supported application routing uses `TrustedLocalCommandRoutingService`.
  `LocalCommandTextRouter` remains a valid low-level component for tests,
  explicit composition, and the three approved historical demos.
- Public HTTP, legacy `/knowledge`, and `CognitiveEngine` do not own or invoke
  Sprint 27 trusted-host routing.
- Sprint 27 adds no schema, dependency, provider, network, clock, or randomness
  requirement. Architecture tests enforce these boundaries.

| Decision / guardrail | Reason | Impact | Source | Status |
|---|---|---|---|---|
| Exact-key discovery is bounded, ordered, and uses the existing knowledge-read permission. | Preserve deterministic local behavior and avoid unrestricted enumeration. | Maximum 50 visible records, one lookahead row, zero-match success, no pagination or cognitive fallback. | Sprint 26 accepted contract and tests | Functional merge `54e04261933ab85dbe4b237e6f81037d508b4a1c`; fully released from canonical `master` at `ae13c3ed9720ee9564384366f2110670eb88fd85`, annotated tag `sprint-26-complete`; Sprint 26 is the prior completed tagged release |
| Knowledge commands use an exact JSON object and request-supplied workspace. | Preserve existing typed knowledge fields without inference or ambiguous delimiters. | Invalid payloads are terminal; provenance remains caller-supplied. | Sprint 25 implementation and tests | Completed/tagged through PR #24 at merge `1f2da9cfb60a06cb323f30f200720be6437e10a9`, tag `sprint-25-complete`; formal ADR governance pending |
| Interpret only the explicit generic list grammar. | Establish a deterministic application boundary without claiming broad language understanding. | Malformed `list` commands are terminal; unrelated text requires explicit cognitive authorization. | Sprint 24 implementation and tests | Completed/tagged at merge `fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`; formal ADR governance pending |
| Local deterministic capability precedes model reasoning for typed supported intents. | Preserve offline operation, authorization and provider independence. | Handled success, denial and validation failure make zero model/external calls. | `docs/02_Local_First_Knowledge_and_Model_Policy.md` | Normative in Sprint 21; formal ADR governance pending |
| Durable adapters point inward to Core repository contracts. | Keep SQLite replaceable and the Core infrastructure-independent. | `app/cognition` must not import `sqlite3`; storage opens only through explicit composition. | Sprint 22 implementation and architecture tests | Completed/tagged at `9dcb36b`; formal ADR governance pending |
| Knowledge storage does not certify truth. | Preserve epistemic honesty. | Provenance is mandatory; no confidence inference, overwrite, semantic retrieval or automatic learning. | Local-first policy and typed knowledge models | Completed/tagged at `9dcb36b`; formal ADR governance pending |
| Local-to-cognitive routing requires explicit caller authorization. | Make local-first priority executable without hidden model fallback. | Handled local outcomes are terminal; only `not_handled` with valid input and authorization may call the cognitive processor. | Sprint 23 coordinator and tests | Completed/tagged at merge `be59175c201df1f2458551d99e2f5dcc3e9d2aac`, tag `sprint-23-complete`; formal ADR governance pending |
| The LLM is not the Core; models are replaceable reasoning providers. | Preserve platform ownership, memory continuity, and provider independence. | Provider changes must not redesign the Core. | `docs/00_Product_North_Star.md`; `docs/01_Cognitive_Lifecycle.md`; `app/cognition/providers/base_provider.py` | Vigente |
| The Core is domain-independent. | One reusable platform must govern multiple products. | Client/domain logic stays outside the Core. | `docs/00_Product_North_Star.md`; `docs/01_Cognitive_Lifecycle.md` | Vigente |
| HealthBridge consumes Luxiom; it is not part of the Core. | It is the first validation of the multi-product architecture. | No HealthBridge exception or coupling in Core code. | `docs/00_Product_North_Star.md` | Vigente |
| New skills are reusable capabilities. | Capabilities persist while tools and technologies change. | Avoid isolated client features in the Core. | `docs/00_Product_North_Star.md`; `docs/foundation/PRINCIPLES.md` | Vigente |
| Specialists create plans and do not execute tools. | Separate domain planning from reusable execution. | Specialists depend on capability concepts, not infrastructure. | `docs/01_Cognitive_Lifecycle.md`; `app/cognition/specialists/specialist.py` | Vigente |
| `CognitiveEngine` orchestrates rather than owning business logic. | Keep stages independently evolvable and testable. | Domain/execution policy belongs behind collaborators. | `docs/01_Cognitive_Lifecycle.md`; `app/cognition/engine.py`; `docs/architecture/Architectural_Invariants.md` (Draft) | Vigente in current runtime |
| `Container` is the Composition Root. | Centralize construction and dependency wiring. | Long-lived services are assembled in `app/core/container.py`. | `app/core/container.py` | Vigente |
| Documentation and executable architecture must stay aligned. | Prevent false architectural claims and recovery errors. | Record mismatches and update operational documents with runtime changes. | `docs/Documentation_Structure.md`; repository recovery requirements | Vigente |
| Material architecture changes require an ADR. | Preserve rationale and consequences over time. | Do not treat implementation or chat as architectural approval. | `docs/Documentation_Structure.md`; `docs/architecture/Architecture_Decision_Record_Standard.md` (Draft) | Pendiente de ADR governance approval |
| A new abstraction should not remain isolated across multiple sprints. | Avoid accumulating unused architectural scaffolding. | Integrate, formally defer, or reconsider abstractions during planning. | Architecture review context supplied for this recovery pack; no approved ADR found | Provisional / pendiente de ADR |

## Application rule

When a source marked Draft conflicts with approved product documents or
executable/tests, do not silently promote the draft. Follow
[Source of Truth](09_SOURCE_OF_TRUTH.md), record the discrepancy, and seek a
formal decision where architecture would change.

## Sprint 28 released permanent decisions

These decisions are implemented in immutable release `sprint-28-complete` at
`be22ffddda6d6961497c338caadf4c85e0fcb3ed` and remain subject to future ADR
governance without weakening the released boundaries.

- Membership is neither authentication nor `PermissionPolicy`.
- Canonical identities and exact case-sensitive actor/workspace pairs are used.
- State is ACTIVE/INACTIVE only; no delete; create does not reactivate.
- SQLite stores durable current state, not audit history.
- Default Container is in-memory/no-I/O; durability is explicit injection.
- Schema v1→v2 migration is additive and explicitly transactional.
- Public transport and authentication remain deferred.
# Sprint 29 released decisions and guardrails

- Authentication proof is opaque.
- `PrincipalIdentity` and `ActorIdentity` are distinct; mapping is explicit.
- Workspace is selected only after successful mapping.
- Membership admission and `PermissionPolicy` authorization are separate.
- A trusted binding selector is not authentication.
- No public transport or production credential technology is included.
- No SQLite authentication persistence is included.
- Configured authentication is local, process-local, nonpersistent, and
  development/test/demo oriented; production credentials remain deferred.
- Authentication is separate from membership and action authorization;
  workspace selection is not admission, membership is workspace admission
  only, and `PermissionPolicy` is action authorization.
- On the verified Windows `core.autocrlf=true` configuration, `git archive`
  converted LF blobs to CRLF. Sprint 29 byte-identical backup used
  `RAW_GIT_BLOB_BYTES`; this guardrail is limited to the verified evidence.

## Sprint 30 released decisions and guardrails

These decisions are implemented in the governed Sprint 30 release at
`6181f549c12195c69708ee2cfa53399a46fa4b29`, immutable annotated tag `governed-sprint-30-complete` (tag object `cd410e5e0ddad708cd3b1a8b91b0fe4dc38e5f35`).

- Durable persistence is added only for
  `PrincipalIdentity -> ActorIdentity`.
- Authentication is not principal mapping.
- Principal mapping is not workspace membership.
- Principal mapping is not action authorization.
- `PrincipalIdentity` remains distinct from `ActorIdentity`.
- One principal may map to at most one actor.
- Multiple principals may map to the same actor.
- Principal lookup is exact and case-sensitive.
- Missing mapping fails closed.
- Repository/storage failure fails closed with the distinct
  `principal_mapping_resolution_failed` outcome.
- Durable mapping storage never authenticates a principal.
- Durable mapping storage never proves workspace membership.
- Durable mapping storage never grants an action permission.
- Mapping persistence stores no credential, proof, verifier, secret, token,
  role, permission, workspace, membership state, or session.
- Mapping creation is append-only for a principal; no update, delete, upsert,
  or overwrite path is introduced.
- Default `Container` remains no-I/O.
- SQLite durability requires explicit caller-owned repository injection.
- `Container` remains the sole application composition root for
  `RepositoryPrincipalActorMapper`.
- Core principal-authentication code must not import SQLite.
- Public HTTP, `CognitiveEngine`, the trusted route, membership semantics, and
  downstream `PermissionPolicy` remain unchanged.
- The deterministic durable demo is operational proof, not a public product
  authentication surface.
- SQLite schema v3 permits only the primary-key UNIQUE constraint on exact
  `principal_id`; additional UNIQUE indexes, including expression indexes, are
  rejected by schema verification.
- The authoritative release backup is `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_SPRINT30_20260819_173314` and was recovered through
  both a full Git bundle and a byte-identical raw-Git-blob source ZIP.
- The historical legacy tag `sprint-30` remains historical evidence only. Its
  object `d5794405f4a0c70dc750e7e4438ca7c10a198b04` still peels to `a37dc884bd7b9962a5842037b52f2bf202f16b34` and must never be
  mutated or reused for the governed release.

The release passed 1,059 post-merge repository tests plus Ruff and the governed
deterministic operational/SQLite validations.

Manual same-assistant governance reviews in this cycle are explicitly distinct
from independent review.

## Sprint 31 governed decisions and guardrails

The following guardrails are implemented in the governed Sprint 31 release:

- Action authorization remains separate from authentication.
- Action authorization remains separate from principal-to-actor mapping.
- Action authorization remains separate from membership admission.
- Membership never implies an action grant.
- Durable grant identity is exactly actor + workspace + action.
- Matching is exact and case-sensitive.
- No wildcard permission matching is introduced.
- No inheritance or role hierarchy is introduced.
- Missing grant fails closed.
- Declared permission-repository failure fails closed.
- Invalid repository output fails closed.
- Unexpected programming errors are not silently swallowed.
- Exact duplicate creation raises PermissionGrantConflict.
- Creation is append-only.
- No update, delete, revoke, overwrite, replace, ignore, or upsert path exists.
- SQLite stores no role, credential, proof, secret, token, session, expiry, or
  permission history.
- Default Container remains no-I/O.
- Durable permission state requires explicit repository injection.
- Configured grants and an injected repository cannot be mixed.
- Core local-resolution code does not import SQLite.
- Authentication and membership domains do not own permission persistence.
- Public HTTP and CognitiveEngine remain unchanged.
- The trusted route remains unchanged.
- The durable demo is operational proof, not a public permission-management API.

These statements are governed Sprint 31 implementation-release truth at
`governed-sprint-31-complete`. Independent implementation review was unavailable
and is not claimed. Release-truth integration and canonical validation are
complete. Closure-truth PR #42, final canonical validation, and governed
working-branch cleanup also completed. Formal Sprint 31 governance closure
conditions were satisfied at canonical checkpoint
`fa90defc44ad756a33f11e470105db57a440e201`; all guardrails remain unchanged.

## Sprint 32 governed decisions and guardrails

The following guardrails are implemented in the governed Sprint 32 release at
`governed-sprint-32-complete`.

- The application boundary is `app/local_command`.
- `app/api` may depend on `app/local_command`; the application boundary points
  inward toward the existing governed routing service.
- The application gateway does not own authentication, principal mapping,
  membership, permission persistence, knowledge storage, model providers, or
  network policy.
- One application request produces exactly one governed routing invocation.
- Authentication proof remains opaque and secret-aware.
- Proof material must not be represented through ordinary repr,
  serialization, logging, or tracing paths.
- Pickle serialization of the application request is explicitly rejected.
- Workspace selection remains explicit.
- Membership remains workspace admission only.
- `PermissionPolicy` remains downstream action authorization.
- Membership never implies an action grant.
- Cognitive fallback remains explicit and caller-authorized.
- Cognitive fallback is never automatic.
- Local validation failure maps to a controlled safe application outcome.
- Unexpected application invariants are sanitized by the HTTP adapter.
- `POST /local/command` is a bounded local-use development surface, not a
  public-Internet authentication API.
- Historical `/brain/think` remains a separate `CognitiveEngine` route.
- Legacy `/knowledge` remains separate.
- Sprint 21 is not retroactively redefined as an HTTP-exposed capability.
- Default `Container` remains rejecting, fail-closed, in-memory, and
  construction-time no-I/O.
- Sprint 32 introduces no runtime SQLite credential composition.
- Sprint 32 introduces no production credential technology.
- Sprint 32 introduces no JWT/OAuth/session/device lifecycle.
- Sprint 32 introduces no roles or RBAC.
- Sprint 32 introduces no public permission-management surface.
- Sprint 32 introduces no public Internet exposure, CORS, or UI.
- The immutable governed implementation checkpoint remains
  `08c15e3ee225c4cdb2f382af5464da01d33d3f6d`.
- Later documentation commits may advance `master` without moving or redefining
  the governed Sprint 32 tag.

The first independent implementation review identified two HIGH findings:
pickle-serializable proof material and incorrect initial external-manifest hash
semantics. Both were corrected and explicitly closed before release.

Sprint 32 is formally governance-closed. These released guardrails do not
authorize any subsequent implementation sprint.
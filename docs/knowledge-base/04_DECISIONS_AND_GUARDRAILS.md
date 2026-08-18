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
# Sprint 29 candidate decisions and guardrails

- Authentication proof is opaque.
- `PrincipalIdentity` and `ActorIdentity` are distinct; mapping is explicit.
- Workspace is selected only after successful mapping.
- Membership admission and `PermissionPolicy` authorization are separate.
- A trusted binding selector is not authentication.
- No public transport or production credential technology is included.
- No SQLite authentication persistence is included.

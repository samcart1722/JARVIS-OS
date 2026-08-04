# Decisions and Guardrails

No approved ADR records were found in the repository. The ADR standard itself
is a draft and `docs/adr/` does not exist. The following consolidation therefore
preserves the status and source of each statement rather than inventing ADRs.

| Decision / guardrail | Reason | Impact | Source | Status |
|---|---|---|---|---|
| Knowledge commands use an exact JSON object and request-supplied workspace. | Preserve existing typed knowledge fields without inference or ambiguous delimiters. | Invalid payloads are terminal; provenance remains caller-supplied. | Sprint 25 implementation and tests | Feature working tree; formal ADR governance pending |
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

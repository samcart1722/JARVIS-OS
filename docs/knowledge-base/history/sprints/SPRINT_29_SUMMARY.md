# Sprint 29 — Local Principal Authentication Foundation v1

## Purpose and architecture

Sprint 29 delivers `LocalAuthenticationProof` → `LocalPrincipalAuthenticator`
→ `AuthenticatedPrincipal` / `PrincipalIdentity` → `PrincipalActorMapper` →
`ActorIdentity` → explicit `WorkspaceIdentity` selection →
`MembershipDecisionService` → existing local routing → `PermissionPolicy` →
capability execution. Authentication precedes mapping; mapping precedes
workspace selection; workspace selection precedes membership; membership
precedes routing; and `PermissionPolicy` remains downstream action
authorization. Authentication, membership, and authorization are distinct;
`PrincipalIdentity` is not `ActorIdentity`, actor identity is not identity
proof, workspace identity is not access proof, workspace selection is not
membership, and membership is workspace admission only.

The binding-key trusted request-context route remains internal, separate, and
non-authenticated. Its `binding_key` is a lookup/trust selector, not an
authentication credential, identity proof, or membership proof. Authenticated
routing does not delegate to trusted routing.

The configured authenticator is deterministic, process-local, nonpersistent,
and development/test/demo oriented. Proof is opaque; verifier matching is exact
and case-sensitive and uses constant-time `hmac.compare_digest`. Proof and
verifier material are neither emitted nor persisted.

`ConfiguredPrincipalActorMapper` provides deterministic configured
`PrincipalIdentity` → `ActorIdentity` mapping for local/demo composition.
Principal IDs are exact and case-sensitive; missing principals fail mapping,
duplicate principal configuration is rejected, and multiple principals may map
to one actor. Mapping is process-local/configured—not durable principal
persistence, authentication, membership, or permission authorization.

Production credentials, public FastAPI authentication, JWT/OAuth, sessions,
durable authentication/credential/principal/mapping state, recovery and account
lifecycle, device/biometric authentication, remote identity, and multidevice
authentication remain deferred. SQLite remains schema v2.

## Release and validation evidence

- Base: `779a2719eaf83de2f98134cc76027dd6f2e7d945`
- Feature branch: `feat/sprint-29-local-principal-authentication-foundation`
- Feature commit: `8f08583701571e69b6d18a0cfea64d073201a217`; PR `#34`
- Merge: `9590beca0ddfce544f774ffc1327d01f8044a420`
- Tree: `57914fd7451d2c5c1c46251bfc7721cc06f8461a`
- Tag: `sprint-29-complete`
- Annotated tag object: `c3a204555cc512ae9404039aeb8be8d6aa421550`
- Tag peel target: `9590beca0ddfce544f774ffc1327d01f8044a420`
- 28-path fingerprint: `0210c787df64fec2f44d5004309d3f73ea5aabfac1322792b0ea34c2c1742b73`

Validation passed 75 authentication, 39 Container, 9 demo-unit, 104
architecture, 129 trusted/membership, 278 focused, and 1,035 repository tests;
Ruff passed. The authenticated 8/8 demo counters were `8/7/5/3/2/1/0` for
authenticator/mapper/membership/router/permission/repository/cognitive. The
trusted demo passed 7/7. Remote counters and proof/verifier leakage were zero.

Architecture enforcement in
`tests/architecture/test_principal_authentication_boundaries.py` covers the
reviewed import, constructor, provenance, and composition controls that prevent
bypassing the intended authentication path. Final architecture validation was
104 passed.

## Authenticated demo scenarios

| Scenario | Expected result |
|---|---|
| `authenticated-active-permitted` | `local_success` |
| `authentication-failure-precedes-invalid-workspace` | `authentication_failed` |
| `mapping-failure-precedes-invalid-workspace` | `principal_mapping_failed` |
| `workspace-selection-invalid` | `workspace_selection_invalid` |
| `membership-not-found` | `membership_not_found` |
| `membership-inactive` | `membership_inactive` |
| `authenticated-active-permission-denied` | `local_permission_denied` |
| `authenticated-payload-workspace-override-rejected` | `invalid_knowledge_fields` |

All eight scenarios passed (`8 / 8 PASS`). Cumulative counters were
authenticator `8`, mapper `7`, membership `5`, router `3`, permission `2`,
repository `1`, and cognitive `0`. Model, provider, readiness, and network
counters were each `0`; proof/verifier leakage was `0`.

## Backup evidence

The sole authoritative backup is
`C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_141402`. Bundle, raw Git-blob ZIP,
and manifest SHA-256 values are `21f6ede11b901891f871854182aa7998ad9fd16f3ab269adf8d01436ea679e7c`,
`d6b2a6b3434514357621aef90c224a88a94c0dd9a49ea0024c68d6b9ee3e4441`, and
`95a23b025654d269d55e392833a5eda843f0043420fd37a8436120761b9c9438`.
Raw-blob verification was 518/518 with zero mismatch/missing/extra.

The earlier `C:\PROYECTOS\LUXIOM_BACKUPS\LUXIOM_20260818_140013` attempt is permanently
`FAILED_VERIFICATION / NON_AUTHORITATIVE_RELEASE_BACKUP`. Git archive under the
verified Windows `core.autocrlf=true` configuration produced 460/460
CRLF-only mismatches through confirmed Git-archive worktree conversion, with
zero release-tree corruption. Its hashes and diagnostic fingerprint are
forensic only, not release evidence. Sprint 30 remains only the next planning /
contract-definition boundary; no Sprint 30 branch, contract, blocks, acceptance
criteria, implementation, or release date is established here.

# Sprint 27 Summary — Trusted Request Context Foundation v1

Status: pre-release; technical implementation approved for release governance.

Final independent implementation re-review: `APPROVED`.
Blocking defects: none. Required corrective work: none.

## Objective and delivered capability

Sprint 27 establishes an internal, deterministic trusted-host request boundary
that resolves configured actor and explicitly requested workspace context before
the supported local text-command route. It adds immutable boundary values, a
transport-neutral resolver port, a configured resolver, a trusted routing
service, Container composition, architecture enforcement, an internal demo,
and supporting architecture, policy, operations, and knowledge-base
documentation.

This is not public authentication. A binding key is an opaque configured lookup
selector, not a credential or authentication proof. `ActorIdentity` is not
proof of authentication, `WorkspaceIdentity` is not proof of access, a
configured binding is not durable membership, and `TrustedRequestContext` is
not an authenticated session. Trust resolution does not grant permission or
replace authorization; `PermissionPolicy` remains downstream.

## Implementation inventory

The new `app/cognition/trusted_context/` package contains:

- `models.py`: immutable host input, trusted context, resolution, binding, and
  trusted routing request/result values;
- `contracts.py`: the transport-neutral `TrustedRequestContextResolver` port;
- `resolver.py`: deterministic `ConfiguredTrustedRequestContextResolver`;
- `routing.py`: `TrustedLocalCommandRoutingService` sequencing;
- `__init__.py`: the approved package surface.

The nine approved production concepts are:

- `TrustedHostRequestInput`
- `TrustedRequestContext`
- `TrustedRequestContextResolution`
- `TrustedRequestContextResolver`
- `ConfiguredTrustedHostBinding`
- `ConfiguredTrustedRequestContextResolver`
- `TrustedLocalCommandRequest`
- `TrustedLocalCommandRoutingResult`
- `TrustedLocalCommandRoutingService`

Stable trust failures are:

- `trusted_context_invalid_input`
- `trusted_context_unknown_binding`
- `trusted_context_unknown_workspace`
- `trusted_context_workspace_not_bound`
- `trusted_context_resolution_failed`

## Trust and resolver semantics

`TrustedHostRequestInput` contains only an opaque binding selector and an
explicit requested workspace ID. Successful resolution returns a frozen,
slotted actor/workspace context without an error. Failure returns no context
and exactly one approved trust error.

The configured resolver rejects duplicate binding keys, duplicate known
workspace IDs, and bindings to unknown workspaces. Lookup trims surrounding
whitespace and remains case-sensitive. There is no implicit or default
workspace and no actor-ID trust shortcut. Unknown workspaces and known but
unbound workspaces remain distinct. Configuration is immutable process state,
with no runtime grant/revoke, persistence, clock, randomness, provider, model,
or network behavior.

## Supported routing and Container composition

The supported conceptual flow is:

```text
TrustedHostRequestInput
  -> TrustedRequestContextResolver
  -> TrustedRequestContext
  -> TrustedLocalCommandRoutingService
  -> LocalCommandTextRouter
  -> deterministic interpretation
  -> LocalFirstCognitiveCoordinator
  -> PermissionPolicy / local resolution
  -> capabilities / repositories
```

Trust failures stop before `LocalCommandTextRouter`. Trust success is not
authorization success: the internal demo proves that a valid trusted context
can still produce downstream `local_permission_denied`.

`Container` accepts tuple-only configured bindings and known workspaces, or an
optional injected resolver. Mixed configured/injected ownership is rejected;
a deliberately falsey injected resolver is preserved through identity
semantics. Each Container owns one resolver and one
`TrustedLocalCommandRoutingService`, reuses the existing
`LocalCommandTextRouter`, and leaves the existing `PermissionPolicy`
unchanged. Empty default trust configuration is inert, and construction does
no external work.

## Architecture guardrails

`tests/architecture/test_trusted_context_boundaries.py` enforces transport
neutrality; infrastructure, persistence, Settings, provider, model, network,
clock, and randomness isolation; lower-layer dependency direction;
authorization/coordinator/repository/capability separation; public API and
`CognitiveEngine` isolation; domain independence; and the direct
`TextRoutingRequest` constructor rule.

The exact approved production/runtime direct-constructor sites are:

1. `app/cognition/trusted_context/routing.py`
2. `app/operations/local_command_interpretation_demo_runtime.py`
3. `app/operations/local_knowledge_command_demo_runtime.py`
4. `app/operations/local_knowledge_discovery_demo_runtime.py`

The Sprint 27 demo is not a fifth site. `LocalCommandTextRouter` remains a
valid low-level component rather than a private API.

Architecture enforcement was corrected after initial alternate-import
false negatives and subsequent lexical false positives. The final
provenance-aware rule detects all five prohibited direct, aliased, re-export,
and module-qualified downstream cases while accepting all four required
benign name/attribute cases.

## Internal demo

The demo consists of
`app/operations/trusted_request_context_demo_runtime.py`,
`scripts/demo_trusted_request_context.py`, and
`docs/operations/TRUSTED_REQUEST_CONTEXT_DEMO.md`. The CLI obtains
`container.trusted_local_command_routing_service`; low-level wrapping is used
only for observation.

The seven validated scenarios are:

1. valid permitted local command: `local_success`;
2. unknown binding: `trusted_context_unknown_binding`;
3. unknown workspace: `trusted_context_unknown_workspace`;
4. known but unbound workspace: `trusted_context_workspace_not_bound`;
5. explicit second workspace: returns `item-beta` and excludes primary-only
   `item-alpha`;
6. successful trust followed by downstream `local_permission_denied`;
7. payload workspace override rejected by the existing interpreter as
   `invalid_knowledge_fields`.

For scenarios 2–4, router, permission, repository, and cognitive call deltas
are all zero. The final demo reports zero model, provider, readiness, and
network calls, supporting deterministic local-first behavior.

## Final validation evidence

| Validation | Final independently approved result |
|---|---:|
| Trusted-context tests | 84 passed |
| Container tests | 21 passed |
| Block F architecture tests | 8 passed |
| Complete architecture suite | 70 passed |
| Routing/coordinator tests | 36 passed |
| Demo runtime tests | 2 passed |
| Demo CLI tests | 2 passed |
| Combined demo tests | 4 passed |
| Focused Sprint 27 suite | 117 passed |
| Full repository suite | 836 passed |
| Ruff | All checks passed |
| Diff check | passed |
| Architecture adversarial matrix | prohibited 5/5; allowed 4/4 |

The manual demo exited 0 with seven scenarios, seven `PASS` statuses,
`Overall: PASS`, and zero model/provider/readiness/network calls. Final
post-review hygiene found no architecture `__pycache__`, no repository-scope
`.pyc`, and no review-generated artifact.

## Protected surfaces and exclusions

Sprint 27 does not integrate trusted routing into public HTTP,
`/brain/think`, legacy `/knowledge`, FastAPI middleware, or `CognitiveEngine`,
and adds no header, token, or session mapping. It does not alter public API
routes, identity definitions, `PermissionPolicy` semantics, repositories,
SQLite schema/version, Alembic, Settings or dependencies, interpreter grammar,
coordinator semantics, providers/network, or auth/login/JWT/OAuth/session/RBAC.

## Deferred work and technical debt

Public authentication, hostile-caller identity proofing, accounts and
sessions, durable membership, HTTP/transport integration, public route
protection, JWT/OAuth/API-key mechanisms, and persistence-backed trusted-host
configuration remain explicitly deferred. They are not Sprint 27 defects.

Final independent review identified no new uncontrolled technical debt. This
does not imply that no future work remains.

## Repository evidence before summary creation

- Canonical `master` / `origin/master` HEAD:
  `d368a0734a0161ad90221c1b5d275dfabfe69cfb`
- Latest completed release: Sprint 26, annotated tag
  `sprint-26-complete`
- Sprint 26 tag object: `fc8b8a403e920f547a72783a296bd7ef406e7033`
- Sprint 26 peeled release commit:
  `ae13c3ed9720ee9564384366f2110670eb88fd85`
- Approved Sprint 27 working tree before this summary: 12 tracked
  modifications, 15 visible untracked files, 0 staged files, 0 deleted
  tracked files, 0 unexpected artifacts, and 0 review-generated ignored
  artifacts.
- Expected working tree after this summary: the same 12 tracked modifications
  and 16 visible untracked files, with this summary as the sole addition.

Inherited ignored root `.pytest_cache` and `.ruff_cache` directories predated
the final review and are not Sprint 27 artifacts.

## Release governance status

- Technical implementation and independent review: `APPROVED`
- Release operations: pending
- Commit: not yet created
- Push: not yet performed
- PR: not yet created
- Merge: not yet performed
- Tag: not yet created
- Final backup: not yet performed

Sprint 27 remains **PRE-RELEASE**. No Sprint 27 commit SHA, PR number, merge
commit, release tag, release date, backup path, or branch-cleanup event exists
yet.

## Final technical conclusion

Sprint 27 — Trusted Request Context Foundation v1 is technically complete and
approved for release governance. Release status must remain pending until the
separately governed Git, tag, verification, backup, and canonical-state steps
actually succeed.

# Internal Trusted Request-Context Demo

## Purpose and scope

This developer-facing demo proves the internal trusted-host routing boundary
locally and deterministically. It exercises configured request-context
resolution, pre-routing trust failures, explicit workspace isolation,
downstream permission separation, and the existing payload-workspace
rejection rule.

This is not authentication. The configured binding key is an opaque lookup
selector, not a credential, password, token, API key, or identity proof. The
demo has no public HTTP exposure and is not a production authentication
scheme.

## Run the demo

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\demo_trusted_request_context.py
```

## Scenarios

1. **Valid permitted local command:** trust resolves for the explicitly
   requested primary workspace and the deterministic local result succeeds.
2. **Unknown binding:** returns `trusted_context_unknown_binding` before the
   low-level router is called.
3. **Unknown workspace:** returns `trusted_context_unknown_workspace` for a
   workspace absent from configured known workspaces.
4. **Known but unbound workspace:** returns
   `trusted_context_workspace_not_bound` for a known workspace outside the
   binding's allowed set.
5. **Explicit second workspace:** explicitly selects a second bound workspace
   and returns only its isolated data.
6. **Trust success followed by permission denial:** trust succeeds, downstream
   authorization runs, and the existing `local_permission_denied` result is
   preserved.
7. **Payload workspace override rejection:** trust succeeds, then the existing
   interpreter rejects a workspace-bearing knowledge payload with
   `invalid_knowledge_fields` before repository access.

## Expected safe output

A successful run prints seven stable scenario identifiers, seven `PASS`
statuses, stable result/error codes, safe router-call counts, and `Overall:
PASS`. Model, provider, readiness, and network totals are all zero. Output does
not include the raw binding selector or configured binding objects.

The demo runs without Internet, Ollama, an external model API, Redis, a
FastAPI server, or an external database server. It uses configured process
state and in-memory local data.

## Safety boundary

This demo is not evidence that public HTTP is authenticated. Sprint 27 does
not connect headers, tokens, `/brain/think`, or legacy `/knowledge` to the
trusted-host boundary. Do not expose the binding key as a public security
mechanism or deploy this configuration as authentication.

## Sprint 28 admission update

The original seven scenarios remain valid, but trusted success alone no longer
permits routing: active membership is required first. Permission remains a
separate downstream decision. The binding selector is not a credential, and
neither this demo nor Sprint 28 authenticates public HTTP.

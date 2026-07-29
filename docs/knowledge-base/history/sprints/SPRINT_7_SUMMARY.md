# Sprint 7 Summary — Reasoning Provider Configuration v1

## Implemented settings

The official `Settings` now defines:

- `OLLAMA_BASE_URL`, default
  `http://localhost:11434/api/generate`;
- `OLLAMA_MODEL`, default `llama3.2:3b`;
- `OLLAMA_TIMEOUT_SECONDS`, default `120`, validated as greater than zero.

Pydantic Settings supports environment overrides. `.env.example` documents
only these non-sensitive defaults; no credentials or real secrets were added.
Independent Settings instances read their own environment state.

## Composition boundary

The runtime now composes:

`Settings → Container → OllamaClient → OllamaProvider → ReasoningStage →
ReasoningCapability`

`OllamaClient(base_url, model, timeout_seconds)` receives all values explicitly.
`OllamaProvider(client)` receives the configured client. Neither reads
environment variables or imports global Settings. `ModelManager` was also
changed to require an injected client, removing its parallel implicit client
construction.

The client and provider perform no network operation during construction.
Network remains limited to `OllamaClient.chat`.

## Compatibility

`ReasoningProvider.generate(context)`, `ReasoningResult`, `ReasoningStage`,
`ReasoningCapability`, registry, executor, specialist, and HTTP contracts are
unchanged. `DefaultSpecialist` continues requesting `normalized_input`; public
requests return deterministic input and do not contact Ollama.

## Verification

Baseline: **34 passed, 1 warning in 1.05s**.

Final: **45 passed, 1 warning in 1.23s**, executed with the versioned valid
setting `DEBUG=true`. The ambient local value `DEBUG=release` is invalid for
the pre-existing boolean field and is documented separately rather than
weakening validation. The warning is the pre-existing pytest cache-path issue.

Tests cover defaults, individual environment overrides, positive-timeout
validation, instance independence, explicit client/provider construction,
configured Container composition, no network during construction, reasoning
compatibility, and the unchanged public route. No Ollama server or network is
required.

## Pending

Public activation and provider-selection policy remain pending, as do multiple
providers, fallback, retries, streaming, health checks, memory, evidence,
tools, and domain specialists.

No commit was created by Sprint 7.

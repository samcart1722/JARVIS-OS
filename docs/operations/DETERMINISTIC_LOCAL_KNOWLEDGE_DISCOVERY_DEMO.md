# Deterministic Local Knowledge Discovery Demo

Sprint 26 is merged into canonical `master` at
`54e04261933ab85dbe4b237e6f81037d508b4a1c`. Release tag
`sprint-26-complete` is pending; Sprint 25.1 remains the latest completed tagged
release until that tag is created.

Run from the repository root:

```powershell
$env:DEBUG='true'
.\.venv\Scripts\python.exe scripts\demo_local_knowledge_discovery.py
```

The ten deterministic scenarios store two same-key facts; find two records by
key; find the same records by key and kind; return empty success for a
nonmatching kind and missing key; deny an unauthorized find; stop malformed
recognized find text; return safe insufficiency for unrelated unauthorized
text; and invoke one fake cognitive response for unrelated authorized text.

Expected boundaries: two repository stores, zero repository reads, four
repository finds, six total repository operations, one fake cognitive call,
and zero model, external, readiness, and network calls. All
discovery results are nontruncated in the human-readable demo; 50/51/52
boundaries are covered by automated tests.

# Deterministic Local Knowledge Discovery Demo

Feature-tree status: Sprint 26 is implemented but unmerged and untagged. The
released baseline is Sprint 25.1 at `9a61d53`, tag
`sprint-25.1-release-closure`.

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

# Conversation History

It is neither necessary nor desirable to commit every chat message. Preserve
concise summaries of architectural decisions, verified findings, and sprint
closures when they add recovery value.

Use this filename convention:

`YYYY-MM-DD_TOPIC_SUMMARY.md`

Recommended template:

```markdown
# Session Summary — YYYY-MM-DD — Topic

## Repository checkpoint
- Branch:
- Commit:
- Working tree:

## Verified facts

## Decisions made
- Decision:
- Authority/source:
- Consequence:

## Work completed

## Tests and validation

## Open questions / next step
```

Optionally export a complete conversation to PDF or Markdown and store it in
encrypted local/offline storage outside Git, especially if it contains personal
or operational context. Remove secrets before archiving.

Chats and their summaries are secondary historical material. They are not
normative sources and do not override approved documents, ADRs, executable code,
tests, or Git history.

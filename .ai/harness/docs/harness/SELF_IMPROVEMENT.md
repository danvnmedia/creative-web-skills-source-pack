# Provenance-Safe Harness Improvement

## Goal

Learn from real product work without allowing one noisy session to rewrite the operating system.

## Lifecycle

`observed failure -> lesson candidate -> repeated evidence -> confidence/provenance review -> human promotion -> harness-improvement -> tested control`

## Candidate rules

- Default scope is project-local.
- Every observation requires an evidence reference and confidence score.
- Candidate text is secret-redacted.
- Do not store raw code snippets as learning payload.
- Project promotion requires repeated observations and human approval.
- Global promotion requires evidence from multiple distinct project IDs, sufficient confidence, and human approval.
- Promotion writes a curated lesson record only; it never edits a Skill automatically.

## Why this separation matters

A product-specific preference can be useful locally but harmful globally. A successful fix is not automatically a general engineering law. Promotion makes scope, evidence, confidence, and authorship explicit.

## Commands

```bash
python .ai/scripts/lesson_candidate.py capture --id <id> --trigger <trigger> --action <action> --confidence 0.85 --evidence <path-or-id>
python .ai/scripts/lesson_candidate.py status --id <id>
python .ai/scripts/lesson_candidate.py promote --id <id> --scope project --human-approved
```

After promotion, use the `harness-improvement` Skill to decide whether the durable fix is a test, sensor, schema, rule, reference, or compact Skill change. Add a regression test for the motivating failure before shipping a new harness version.

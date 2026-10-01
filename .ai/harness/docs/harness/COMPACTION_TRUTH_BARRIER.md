# Compaction Truth Barrier

v5.4.4 strengthens the v5.3 verified-progress rule: **observed text is not a verified fact**.

Context compaction, session summaries, model switches, and handoffs may carry only claims that already point to fresh passing evidence for the exact workspace. A summary does not become evidence merely because it says a check passed.

## Evidence lineage

New checkpoints use schema 2. Each durable claim contains:

- `claim_status: verified`;
- exact `source_event_ids`;
- supporting check names;
- producer exit statuses;
- closed tool-call/result state;
- verification revision when available.

Evidence events produced by `record_evidence.py` now include a stable `event_id`, `producer_exit_status`, `producer_kind`, and `tool_pair_state`.

A process that prints `PASS` but exits non-zero or is killed/blocked remains failed evidence. It cannot be promoted into a checkpoint milestone. Failed/rejected attempts remain referenced by the checkpoint as evidence rather than disappearing from history.

## Boundary truth

Checkpoint creation labels how capture occurred: `manual`, `instruction_driven`, or `host_hook`. Do not claim hook automation on a host unless an actual hook produced the capture.

After compaction or context refresh, run:

```bash
python .ai/scripts/checkpoint_reverify.py --task <TASK-ID>
```

An optional compaction-summary metadata file may reference verified claim IDs and source event IDs. It may not carry new autonomous `facts`, `claims`, `completed`, or `verified_facts`. Missing source-event coverage, stale checkpoint hashes, source drift, nonzero producer exits, or open tool-call/result pairs fail closed.

The emitted resume digest is bounded by `.ai/COMPACTION_POLICY.json` so durable continuity does not grow into another context dump.

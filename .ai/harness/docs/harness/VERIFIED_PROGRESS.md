# Verified Progress Across Long Work

Long-running work should survive context refresh without preserving unverified claims or hidden reasoning.

A verified checkpoint contains only:

- task id;
- source fingerprint;
- completed observable milestones;
- fresh passing evidence references/digests;
- one safe next action;
- short observable notes.

It must not contain hidden chain-of-thought, full chat transcripts, secrets, provider session objects, or an executor's unsupported claim.

Create checkpoints only at meaningful verified boundaries, not after every command.

```bash
python .ai/scripts/verified_checkpoint.py checkpoint \
  --task TASK-123 \
  --completed "Critical user flow passes on mobile and desktop" \
  --next-action "Run production candidate closure" \
  --check critical-flow
```

Validate before using it as durable evidence:

```bash
python .ai/scripts/verified_checkpoint.py validate --task TASK-123
python .ai/scripts/verified_checkpoint.py resume --task TASK-123
```

If the source fingerprint or referenced evidence changed, resume fails closed. A rejected or failed attempt remains evidence, not progress.

## Compaction truth barrier (v5.4.4)

New checkpoints record stable source event IDs, producer exit status, closed tool-call/result state, and explicit `claim_status=verified`. A failed/killed command remains evidence even if its stdout contains success-like text.

After context compaction/session refresh, run `python .ai/scripts/checkpoint_reverify.py --task <TASK-ID>` before treating the checkpoint as current progress. External summaries may reference verified claim IDs and source event IDs but are not evidence themselves. See `docs/harness/COMPACTION_TRUTH_BARRIER.md`.

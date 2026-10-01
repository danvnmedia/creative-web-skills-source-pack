# Adaptive Execution Profiles

v5.3 separates **product quality requirements** from **persistence ceremony**.

## Profiles

| Profile | Use when | Durable checkpoint |
| --- | --- | --- |
| `native` | Work can finish and verify in the current session. | No |
| `portable` | Work may cross a session/model/context boundary or wait externally. | Yes |
| `audited` | Critical/security/release/harness work needs stronger proof. | Yes |

The profile never removes trait-derived checks. A `native` user-facing web task still needs build, browser, and critical-flow evidence. The profile controls how much durable execution state is materialized, not whether product behavior must be verified.

Resolve the profile after the task contract exists:

```bash
python .ai/scripts/execution_profile.py --task TASK-123 --write
```

`auto` is the safe default. `CRITICAL`, production-release, security-sensitive, harness-modification, or high/critical risk work resolves to `audited`. Cross-session, external-wait, or expected context-refresh work resolves to at least `portable`.

An explicit profile may escalate the derived profile, but may not weaken it.

## Portable/Audited checkpoint

Persist only verified boundaries. First record the checks that prove the milestone, then create and validate a checkpoint:

```bash
python .ai/scripts/verified_checkpoint.py checkpoint \
  --task TASK-123 \
  --completed "Upload replacement survives reload" \
  --next-action "Verify degraded provider fallback" \
  --check state-recovery

python .ai/scripts/record_evidence.py \
  --task TASK-123 --check verified-progress -- \
  python .ai/scripts/verified_checkpoint.py validate --task TASK-123
```

Checkpoint files are runtime state under `.ai/checkpoints/`; they are excluded from source fingerprints and release ownership except for the directory README.

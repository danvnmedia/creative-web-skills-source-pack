# Migrating from v5.2.1 to v5.3.0

v5.3 adds adaptive execution depth, trusted repo mapping, verified-progress checkpoints, Skill runtime-eval contracts, and an optional Agent Plugins skills-only export.

## Preferred upgrade

Extract the trusted v5.3 release outside the project and run:

```bash
python /path/to/Codex_Product_Harness_v5.3/INSTALL_HARNESS.py --target /path/to/project
```

The ownership-aware installer preserves user-modified conflicts by default.

## After upgrade

```bash
python .ai/scripts/bootstrap_project.py --write
python .ai/scripts/harness_doctor.py
python .ai/scripts/surface_drift.py
python .ai/scripts/harness_security.py
python .ai/scripts/validate_harness.py
python .ai/scripts/skill_eval.py validate
python .ai/scripts/self_test.py
```

For an active task, copy any missing fields from the schema-v4 task template, then resolve its execution profile:

```bash
python .ai/scripts/execution_profile.py --task TASK-123 --write
```

Portable/audited tasks now require a fresh `verified-progress` check backed by `.ai/scripts/verified_checkpoint.py`.

If a task changes any shipped Skill, set `traits.skill_modification=true`. A package/metadata pass alone does not establish Skill runtime quality; run a trustworthy live/paired skill eval or use an explicit time-bounded waiver when the host cannot expose suitable telemetry.

For exhaustive historical regression coverage in CI or a dedicated maintenance window, run `python .ai/scripts/self_test_extended.py`.

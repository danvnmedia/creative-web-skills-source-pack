# Operator Command Plane

Normal operation should prefer the boundary-aware router instead of asking an agent to remember low-level scripts:

```bash
python .ai/scripts/harness.py verify --profile native
python .ai/scripts/harness.py verify --profile portable --task TASK-123
python .ai/scripts/harness.py verify --profile audited --task TASK-123 --record-evidence
python .ai/scripts/harness.py cleanup          # dry-run
python .ai/scripts/harness.py cleanup --apply
```

The router detects source-distribution vs installed-runtime context. It never treats `validate_harness.py` as an installed-runtime validator. Source validation stays strict; installed validation uses ownership state. Trait-derived quality checks are never removed by choosing a lighter execution profile.

`--record-evidence` records only checks for which a trusted command mapping exists. Browser, production and external checks remain explicitly pending until real runtime evidence is supplied; pending never counts as pass.

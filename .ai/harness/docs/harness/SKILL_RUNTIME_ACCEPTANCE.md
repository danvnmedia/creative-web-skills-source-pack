# Skill Runtime Acceptance

A `SKILL.md` in a package proves presence, not autonomous activation or causal value. v5.4.1 keeps these claims separate.

1. Contract present: valid Skill metadata and positive/negative routing cases.
2. Activation measured: trustworthy native/trace attribution; self-report or generic file-read inference is rejected.
3. Causal value: paired same-runtime with-Skill/without-Skill runs show no quality regression and either >=5% quality lift or >=5% measured token/duration/cost improvement within explicit budgets.

Validate/prepare routing tests with `skill_eval.py validate` and `prepare`. Grade trustworthy activation telemetry with `report`. Grade causal runs with:

```bash
python .ai/scripts/skill_eval.py causal-report \
  --runs .ai/evidence/skill-causal-runs.jsonl \
  --audit-log .ai/evidence/skill-causal-audit.jsonl \
  --fail-on-regression
```

When a loader, package, or export path changed, also pass `--require-exact-artifact`; at least one paired run must report `runtime.artifact_origin` as `reextracted-zip` or `published-package`. Source-only success cannot prove packaged runtime behavior.

For shipped Skill edits set `traits.skill_modification=true`; `skill-eval-live` remains mandatory unless an explicit human-approved, time-bounded waiver exists. Hidden holdout/holdback splits, deterministic graders before model judges, ablations, leakage checks, flaky-run analysis, and per-Skill cost attribution are preferred for mature CI suites.

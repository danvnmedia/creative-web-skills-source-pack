# Antigravity adapter - Codex Product Harness v5.3

Antigravity is a first-class harness target, but feature parity with Codex/Claude/Gemini must never be assumed.

1. Read `AGENTS.md` first; it is the canonical operating constitution.
2. Read `.agents/rules/00-product-harness.md` before product edits.
3. Use `.agents/workflows/` for start-task, runtime verification, and shipping flows.
4. Load only relevant `.agents/skills/*/SKILL.md` files.
5. Treat `.ai/TASK_TEMPLATE.json` and `.ai/QUALITY.json` as machine policy, not optional prose.
6. If an Antigravity capability differs from another harness, adapt the execution method while preserving the same evidence requirement.
7. Never claim a hook, MCP, agent, browser, or sandbox capability merely because another harness supports it.
8. Resolve the active task with `.ai/scripts/execution_profile.py`; `native` avoids unnecessary persistence, while portable/audited work uses verified checkpoints only.
9. Respect `.ai/REPO_MAP.json`; inferred commands and runtime hints are not executable truth.
10. For Skill changes, follow `.ai/SKILL_EVAL_POLICY.json`; Antigravity self-report is not activation evidence.
11. For harness changes, run `surface_drift.py`, `harness_security.py`, `validate_harness.py`, `skill_eval.py validate`, and `self_test.py` before packaging.

Recommended first instruction:

```text
Read AGENTS.md, .agents/rules/00-product-harness.md, the active task contract,
and .ai/QUALITY.json. Load only relevant .agents/skills. Preserve the same
runtime/evidence gates even when Antigravity uses a different execution surface.
```


## v5.5 operator entrypoint
For normal installed-project verification, run `python .ai/scripts/harness.py verify --profile native` (or `portable`/`audited`). `validate_harness.py` is source-distribution-only.

## v5.5.4 security coverage extension (baseline remains v5.3.0)

Incoming Skill/plugin Python code now receives bounded AST sink analysis in addition to regex scanning. Statically reconstructable reflective `exec`/`eval` is blocking; opaque executable/compiled payloads make static analysis partial and therefore non-clean. Never execute an untrusted payload merely to improve scan coverage. See `.ai/harness/docs/SECURITY_COVERAGE_V5_5_4.md`.

## v5.5.3 completeness extension (baseline remains v5.3.0)

Required deterministic Harness release regressions are auto-discovered; partial security analysis is never clean; catalog-routing fixtures are not live Skill activation proof; and host-surface snapshots must be pinned before drift classification. See `.ai/harness/docs/TRUTH_COMPLETENESS_V5_5_3.md`.

## v5.5.2 runtime truth extension (baseline remains v5.3.0)

For Skill-runtime, plugin-export, MCP-client or interrupted operator-input work, load
`.ai/harness/docs/TRUTH_HARDENING_V5_5_2.md` only when relevant. Do not treat fixtures, legacy
trace labels, input acknowledgement, or the bundled MCP guard as live host proof.
Before resuming a portable/audited round, inspect an existing operator ledger with
`python .ai/scripts/operator_events.py status`; unresolved claims require explicit
recovery, not automatic action replay. This extension never removes trait gates.

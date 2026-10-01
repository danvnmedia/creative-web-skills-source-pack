# Claude Adapter - Codex Product Harness v5.3

`AGENTS.md` is canonical. Read `.ai/TASK_TEMPLATE.json` and `.ai/QUALITY.json` for machine policy. Use Claude as a fallback executor/reviewer, not as an assumed independent team.

Required behavior:
- resume from `.ai/STATE.json` + `.ai/RESUME.md`;
- use the active task contract and real commands;
- load only relevant `.agents/skills/` content;
- do not claim success without fresh evidence;
- for web work, require actual browser/network evidence;
- for AI integrations, follow `.ai/AI_PROVIDER_POLICY.json` and run contract/failure tests;
- run `.ai/scripts/evidence_gate.py` before completion;
- run `.ai/scripts/loop_guard.py` before repeating an identical failed verification;
- report unavailable checks honestly;
- do not assume hook/MCP/sandbox parity with another harness.

- respect `.ai/REPO_MAP.json`: inferred commands/URLs are not executable truth;
- resolve `native|portable|audited` with `.ai/scripts/execution_profile.py`;
- for portable/audited work persist only fresh evidence-backed milestones via `.ai/scripts/verified_checkpoint.py`;
- for Skill changes follow `.ai/SKILL_EVAL_POLICY.json`; self-report is not activation proof.


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

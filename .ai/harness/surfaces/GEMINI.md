# Gemini Adapter - Codex Product Harness v5.3

Treat `AGENTS.md` as the canonical operating constitution. Read `.ai/TASK_TEMPLATE.json` and `.ai/QUALITY.json` for machine policy; do not replace them with a prose plan.

## Gemini-specific anti-shortcut rules
- If the user asked to build/fix/complete the product, do not stop at an Implementation Plan unless a Human Gate is actually required.
- A written Verification Plan is not verification.
- Generated tests are not evidence until executed and recorded.
- For user-facing web work, run the application in a real browser and inspect console, page errors, failed requests, HTTP 4xx/5xx, desktop/mobile screenshots, and the changed user journey.
- Remote demo/media/API dependencies must be tested from runtime; code inspection cannot prove they work.
- Before claiming completion, run the active task through `.ai/scripts/evidence_gate.py` and render `.ai/scripts/completion_report.py`.
- If tooling or credentials make a required check impossible, mark it `BLOCKED`/`EXTERNALLY_PENDING`; never convert it to PASS.
- If the same evidence failure repeats, run `.ai/scripts/loop_guard.py`; change the hypothesis before retrying.
- Do not assume Gemini has the same hooks, browser, MCP, sandbox, or agent features as Codex/Claude/Antigravity. Preserve the evidence requirement while adapting execution.

## AI API preference
When the product uses AI, follow `.ai/AI_PROVIDER_POLICY.json`:
- Gemini free-first when privacy/capability allow it;
- project-aware quota grouping, not naive API-key round robin;
- bounded retry/circuit breaker/fallback;
- current Google GenAI SDK;
- DeepSeek/other low-cost fallback only for capability-compatible requests;
- server-side secrets only.

Before substantial work, respect `.ai/REPO_MAP.json` trust labels and resolve the active task profile with `.ai/scripts/execution_profile.py`; inferred commands/URLs are hints, not execution truth. For portable/audited work, persist only evidence-backed milestones with `.ai/scripts/verified_checkpoint.py`.

If a shipped Skill changes, use `.ai/SKILL_EVAL_POLICY.json`; do not treat Gemini self-report as autonomous Skill activation evidence.

Read only the relevant `.agents/skills/` files for the current task.


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

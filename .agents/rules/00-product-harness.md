# Product Harness Rule

`AGENTS.md` is the canonical operating constitution for this repository.

For implementation/fix requests, do not stop at a plan unless a real Human Gate is reached. Use the active task contract, run real project commands, and require fresh evidence.

Run `bootstrap_project.py --write` before trusting project commands on a new install; `observed`, `declared`, and `inferred` are different trust levels, and inferred commands/URLs are not execution truth.

Resolve the task with `execution_profile.py`. Native avoids duplicate persistence; portable/audited work persists verified progress only. The execution profile never removes trait-derived product-quality checks.

For user-facing web work, real browser/network evidence is mandatory. For AI work, follow `.ai/AI_PROVIDER_POLICY.json`. Before declaring completion, run `.ai/scripts/evidence_gate.py` for the active task.

If a failed verification repeats, use `.ai/scripts/loop_guard.py` and change the hypothesis before another retry.

If the harness itself changes, set `harness_modification=true` and run harness security, surface drift, package contract, harness self-test, and skill-eval-contract checks. If a shipped Skill changes, also set `skill_modification=true`; self-report is not Skill activation proof.

Learned lesson candidates require provenance and human promotion and must never auto-edit shipped Skills.

# Migration v4 → v5

v4 had a packaging defect: its constitution referenced control-plane files, scripts, and Skills that were missing from the delivered ZIP. v5 replaces those imaginary mechanisms with shipped files and a validator.

## Steps
1. Back up project-specific `.ai/PROJECT.md`, decisions, resume, and task/evidence data.
2. Copy v5 files into the repository.
3. Restore/merge durable project facts.
4. Run `python .ai/scripts/bootstrap_project.py --write`.
5. Inspect `.ai/COMMANDS.json`; remove any detected command that is not truly valid.
6. Configure `.ai/AI_PROVIDER_POLICY.json` if the app uses AI.
7. Run `python .ai/scripts/provider_policy_lint.py`.
8. Run `python .ai/scripts/harness_doctor.py` and `validate_harness.py`.
9. Convert active work to a JSON task contract and set task traits.
10. Re-run fresh verification; v4 statements/tests are not automatically evidence for v5.

## v5 completion-gate tightening
User-facing web tasks now require three distinct proofs: build, generic runtime/browser health, and the changed critical user flow. AI tasks require a deterministic failure matrix plus a live application-path contract check when authorized credentials are available. Critical external runtime dependencies receive their own probe gate.

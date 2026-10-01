# Migration v5.5.9 -> v5.5.10

v5.5.10 is a bounded provider-routing control-plane hardening. It preserves the v5.3.0 canonical baseline, all 13 canonical Skills byte-for-byte, and all v5.5.9 release-doctor/marker/recorder behavior.

## Why

A free or zero-cost requested model can legitimately fall back to a paid target. Budget authorization made only against the requested model is insufficient: the router must evaluate the actual billing target immediately before executing it. Otherwise a zero-cost primary may bypass the budget gate for a paid fallback.

## Changed

- `.ai/AI_PROVIDER_POLICY.json` schema v3 requires actual-target budget evaluation before paid fallback execution.
- `provider_policy_lint.py` keeps v1/v2 compatibility and validates the v3 target-budget/fallback-graph contract.
- `provider_route_budget.py` is an optional pure reference evaluator. It does not call providers, reserve money, or certify an application router.
- `v5510_regression_test.py` covers free-target continuity, paid-target budget denial, atomic-reservation requirement, unknown metadata failure, and lineage/Skill preservation.

## Upgrade

Use the normal plan -> review -> exact digest apply flow. Do not manually copy files over a project installation. Existing v1/v2 project policy remains lint-compatible; adopting v3 should be a reviewed project policy migration rather than a silent behavior change.

## Limits

This release does not modify an application router, make live provider calls, turn on billing, spend paid budget, or prove provider/runtime behavior. Actual budget reservation must be atomic in the application's authoritative spend store; the pure evaluator only models the decision contract.

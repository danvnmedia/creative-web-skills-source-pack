# Release & Production Acceptance Runbook

## 1. Candidate readiness
Before release:
- active task acceptance criteria pass or exceptions are explicitly approved;
- lint/type/tests/build required by repo pass;
- relevant security/accessibility/performance checks pass;
- migration order and backward compatibility are understood;
- config/secrets are present without exposing values;
- rollback path is known;
- release candidate SHA is recorded.
- `.ai/scripts/workspace_hygiene.py --strict --allow-evidence` passes and the source candidate is clean.

## 2. Migration safety
For schema/data changes:
- prefer expand -> migrate/backfill -> switch -> contract;
- avoid requiring old and new app versions to disagree on schema during rolling deploy;
- make long backfills resumable/idempotent where feasible;
- test on representative volume when risk warrants it;
- record recovery plan before destructive cleanup.

## 3. Deploy
- first run required evidence on the candidate and close it with `.ai/scripts/close_task.py`;
- deploy the approved candidate through normal protected workflow;
- do not bypass branch/CI controls to save time;
- record deployed SHA/version;
- verify configuration target/environment.

## 4. Production acceptance
Minimum applicable checks:
- canonical public route responds correctly;
- authenticated/private routes preserve boundaries;
- health/readiness is healthy and does not leak secrets;
- critical value loop smoke test passes using safe test data/account;
- `production-smoke` and `production-critical-flow` are recorded separately;
- static assets/version identify the intended deployment;
- DB/storage/worker/realtime dependencies are ready;
- browser console/CSP/network has no release-blocking error;
- monitoring sees the new version.

Deployment success != production acceptance.

Use `docs/harness/CANDIDATE_CLOSURE.md` for the exact candidate-to-closure commands. A closure-only metadata commit may follow candidate verification, but any product-source change invalidates the closure. An exact-revision probe after closure should be ephemeral so evidence does not create an infinite commit/deploy loop.

## 5. Observe after release
Watch:
- error rate;
- latency;
- auth/permission failures;
- DB/provider health;
- queue/background failures;
- critical user-flow completion;
- cost/quota anomalies.

## 6. Rollback criteria
Rollback or disable the feature when a guardrail is materially violated and mitigation is not safer/faster.

Possible guardrails:
- data corruption/loss;
- auth/tenant boundary failure;
- large error/latency regression;
- primary workflow unusable;
- runaway cost/provider quota;
- serious accessibility/usability regression affecting task completion.

After recovery, write a regression action and update tests/runbook where appropriate.

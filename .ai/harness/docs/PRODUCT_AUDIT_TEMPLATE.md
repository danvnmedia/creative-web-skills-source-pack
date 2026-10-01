# Product Audit Template

Use this when taking over an existing repository, when the product “mostly works” but quality is uncertain, or before a significant launch.

## Audit rules

- Inspect running behavior when possible, not only source code.
- Separate `observed`, `inferred`, and `unknown`.
- Do not fix everything during the audit.
- Every finding needs evidence and user/business impact.
- Rank by consequence and value, not cosmetic preference.

## Severity

- **P0**: security/data-loss/outage/core value loop broken; release blocker.
- **P1**: major usability/correctness/performance/reliability issue affecting primary workflow.
- **P2**: meaningful improvement but product remains usable.
- **P3**: polish/cleanup/optional optimization.

## 1. Product reality
- Primary user/job:
- Core value loop:
- Can it be completed now?
- Evidence/metrics/support signals:
- Major mismatch between product and actual user need:

## 2. UX/UI
Check:
- information hierarchy;
- onboarding/time-to-first-value;
- responsive 320px+ and desktop;
- loading/empty/error/success/permission states;
- keyboard/focus/accessibility;
- forms/validation;
- touch and mobile keyboard;
- long text/locales;
- visual stability and perceived responsiveness;
- destructive action confirmation/undo.

## 3. Correctness/data
Check:
- state transitions;
- validation source of truth;
- stale data/concurrency/double-submit;
- migration integrity;
- idempotency;
- regression coverage of critical workflows.

## 4. Security/privacy
Check:
- authentication/session;
- server authorization and object/tenant isolation;
- input/file/URL handling;
- secrets/config;
- rate/abuse/cost controls;
- sensitive logs/analytics;
- retention/deletion/export;
- dependency/supply-chain posture.

## 5. Performance/scale
Check:
- Core Web Vitals where applicable;
- bundle/media size;
- query count/N+1/unbounded lists;
- pagination/limits;
- cache correctness;
- expensive external calls;
- timeout/retry/backoff;
- background jobs/queues;
- load test/capacity evidence for claimed scale.

## 6. Reliability/operations
Check:
- health/readiness;
- logs/metrics/alerts;
- external provider failure/degradation;
- backup/restore when required;
- rollback;
- production config drift;
- deployment SHA visibility;
- incident/runbook readiness.

## 7. Maintainability
Check:
- duplicated sources of truth;
- oversized modules and hidden coupling;
- dead/deprecated paths;
- testability;
- dependency hygiene;
- docs inconsistent with reality.

## Findings table

| ID | Severity | Dimension | Observation/evidence | User/business impact | Recommended smallest slice |
|---|---|---|---|---|---|
| | | | | | |

## Recommended execution order
1.
2.
3.

Choose the first task by highest combination of risk reduction and user value, not by easiest cosmetic win.

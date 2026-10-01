# Product Quality Contract

This document defines the minimum bar for saying a feature/release is “good”, while `.ai/QUALITY.yaml` stores project-specific targets.

## 1. User value gate
Pass when:
- the primary user can complete the intended job end-to-end;
- the behavior solves the task contract outcome;
- major dead ends are removed;
- success can be observed or measured when appropriate.

## 2. UX/UI gate
Pass when applicable:
- responsive layout is usable on target devices;
- loading/empty/error/success/permission states are designed;
- keyboard and focus behavior works;
- forms provide clear validation and do not lose user input unexpectedly;
- actions have truthful pending/success/error feedback;
- repeated actions/double-submit are safe;
- accessibility target is met with evidence appropriate to the project;
- visual polish does not hide functional/accessibility regressions.

## 3. Correctness gate
Pass when:
- acceptance behavior is deterministic;
- critical domain rules have tests;
- server/data source of truth is authoritative;
- important bug fixes have regression guards;
- baseline failures are separated from change-caused failures.

## 4. Security/privacy gate
Pass when:
- authentication/authorization boundaries are tested where relevant;
- input and files are bounded/validated;
- sensitive data/secrets do not leak to client/logs/source;
- dependencies and configuration do not introduce known unacceptable risk;
- privacy collection/retention aligns with project policy;
- no known high/critical blocker remains.

Use OWASP ASVS 5.0 as the practical verification baseline and OWASP Top 10:2025 as an adversarial awareness checklist.

## 5. Performance/scale gate
Pass when:
- work is bounded;
- critical query/call paths are understood;
- project performance budgets pass where measurable;
- scale claims have load/capacity evidence;
- retries/timeouts cannot create obvious cascading failure;
- large content/media/list behavior is intentional.

For web UI, default good Core Web Vitals targets are LCP <= 2.5s, INP <= 200ms, CLS <= 0.1 at the 75th percentile unless the project sets stricter/different targets.

## 6. Reliability/operations gate
Pass for release when:
- expected provider/database/network failures have defined behavior;
- logging/health/monitoring are sufficient to detect meaningful failure;
- migrations and rollback are understood;
- persistent critical data has appropriate backup/restore evidence;
- production acceptance verifies the intended deployed version.

## 7. Maintainability gate
Pass when:
- change follows existing conventions or records an intentional new decision;
- complexity is proportional to need;
- duplicated source of truth is avoided;
- relevant docs/tests/config are updated;
- no unrelated refactor is hidden in the task.

# Performance, Scale & Reliability Baseline

## 1. Performance begins with user journeys
Measure the flows users care about, not only isolated functions.

For web UI, default Core Web Vitals targets at p75:
- LCP <= 2.5 seconds;
- INP <= 200 ms;
- CLS <= 0.1.

Use project-specific API/job budgets for critical operations.

## 2. Bound the work
Every potentially large operation should have an explicit bound:
- pagination/cursor/limit for lists;
- upload size/count limits;
- query complexity/time limits;
- batch size;
- queue size/concurrency;
- AI token/cost limits;
- export/report limits or background processing.

“No limit because current data is small” is not a scale plan.

## 3. Database/data access
Check:
- indexes for critical predicates/order;
- N+1 patterns;
- unbounded scans;
- transaction boundaries;
- lock/contention behavior;
- connection pool limits;
- pagination stability;
- cache consistency/invalidation.

Optimize based on evidence, not aesthetic preference.

## 4. External dependencies
Every remote call should define as appropriate:
- timeout;
- cancellation;
- retry limit;
- exponential backoff + jitter;
- idempotency/replay behavior;
- circuit/degradation strategy;
- user-visible fallback.

Retries can amplify overload. Never retry indefinitely.

## 5. Side effects and concurrency
For state-changing operations consider:
- idempotency key or duplicate suppression;
- optimistic/pessimistic concurrency;
- race between reads and writes;
- out-of-order events;
- webhook replay;
- retry after ambiguous timeout.

## 6. Graceful degradation
When dependencies/traffic fail, prefer a reduced but useful experience when feasible:
- cached/read-only data;
- disable non-critical personalization/AI enhancement;
- queue non-urgent work;
- shed expensive optional requests;
- return explicit partial/degraded status.

## 7. Load and capacity
Before claiming “handles scale”:
1. define expected normal/peak workload;
2. select representative critical scenarios;
3. load test with realistic data and concurrency;
4. observe latency, errors, saturation, DB/provider behavior and cost;
5. test beyond expected peak enough to understand degradation/failure;
6. document bottleneck and safe operating envelope.

Capacity claims must cite evidence date/version/environment because code and infrastructure change.

## 8. Observability
At minimum for production services:
- request/job error rate;
- latency for critical flows;
- saturation/queue depth where relevant;
- dependency failures;
- database/storage health;
- worker heartbeat;
- product value-loop failure signals;
- quota/cost for paid/AI providers.

Logs should be structured enough to diagnose incidents without leaking secrets/PII.

## 9. Reliability release questions
- What happens if DB/provider is slow?
- What happens if the same request arrives twice?
- What happens if deploy occurs during active work?
- What happens if a migration partially fails?
- Can we rollback app independently from data?
- Can operators distinguish user error from system error?
- Is the health check actually representative?
- Is backup restore proven, not assumed, when data matters?

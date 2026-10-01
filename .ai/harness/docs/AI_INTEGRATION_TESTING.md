# AI Integration Verification Matrix

## 1. Deterministic router tests (no upstream traffic)
Use fake provider adapters and a fake clock.

Required cases when applicable:
- primary success;
- 401 quarantines only the credential;
- 403 does not loop through same broken project indefinitely;
- 404 refreshes/disables stale model;
- 429 short cooldown respects retry timing;
- 429 daily quota marks quota group exhausted;
- 500/503/504/timeouts back off and circuit-break;
- retry budget never exceeds configured total;
- same-project Gemini keys do not count as independent quota groups;
- fallback preserves required capability/schema;
- incompatible fallback is rejected;
- streaming interruption is surfaced/recovered safely;
- duplicate model/tool retry does not duplicate side effects;
- logs redact keys and sensitive bodies.

Record this deterministic suite as `ai-failure-matrix` evidence. A happy-path mock alone is not sufficient.

## 2. Live provider contract test
When authorized credentials exist, run one small real request through the same adapter/router used by the application. Verify:
- current model/resource exists;
- auth works;
- expected response/schema/tool/stream contract is still compatible;
- latency/error mapping works;
- usage metadata is parsed;
- chosen routing metadata is recorded safely.

Record as `ai-contract` evidence.

A mock-only suite cannot prove a provider renamed a model, changed an API surface, or rejected the credential today.

## 3. Product-path test
Test the actual user workflow that consumes AI output, including loading, timeout, partial response, provider unavailable, invalid output, and retry UX.

## 4. Load/failure testing
Use local fake providers or a controlled staging service for load, burst, and retry-storm tests. Do not discover free upstream limits by hammering the provider.

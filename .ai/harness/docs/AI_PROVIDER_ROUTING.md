# AI Provider Routing Architecture

## Design goals
- free/low-cost first where appropriate;
- no secret leakage;
- no provider lock-in in domain logic;
- bounded failure handling;
- observable decisions;
- capability-safe fallback;
- deterministic testability.

## Recommended interfaces
Separate:
- `AIRequest` product contract;
- `ProviderAdapter` protocol translation;
- `CapabilityRegistry`;
- `QuotaGroupState` / circuit breaker;
- `Router` selection/fallback;
- `UsageTelemetry`;
- `ToolExecution` side effects.

This makes routing tests independent of live providers.

## State to track per quota group
- provider/project/model scope;
- health state: healthy/cooldown/exhausted/quarantined;
- in-flight requests;
- rolling success/failure rate;
- latency EWMA;
- last 429 category and recovery time;
- optional local RPM/TPM/RPD estimates;
- last capability refresh.

For multiple application instances, move shared quota/circuit state to Redis/database rather than letting each instance independently hammer the same upstream quota.

## Fallback ladder
A fallback ladder is **capability-specific**, not globally ordered. Example:
- text/code/reasoning: Gemini free → DeepSeek flash/low-cost → approved paid provider;
- image generation: Gemini/image-capable provider only;
- TTS: configured TTS-capable model/provider only;
- tool-heavy structured flow: only providers verified for required tool/schema contract.

## Optional gateway products
LiteLLM and New API can provide a centralized gateway when a project truly needs multi-provider management. Do not add a gateway merely to avoid writing a small adapter; another service adds operational/security surface.

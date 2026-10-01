# Gemini Free-First Routing Standard

## Purpose
Use Gemini's free tier efficiently for eligible workloads without turning key rotation into quota evasion or a reliability hazard.

## Non-negotiable facts encoded by the harness
- Gemini rate limits are scoped **per Google Cloud project**, not per API key. Keys belonging to the same project share the same quota bucket.
- Free-tier eligibility/model limits change; discover or configure current capabilities instead of freezing model names in product logic.
- Use Google's current GenAI SDK (`@google/genai` for JavaScript/TypeScript). Do not start new work on legacy `@google/generative-ai`.
- Provider keys belong on the server, never in browser bundles.
- Free-tier privacy differs from paid tiers. The default harness policy forbids sensitive data on free tier unless the project explicitly changes that decision.

## Recommended topology

```text
Application
   |
   v
AI Provider Router (server-side)
   |
   +-- Gemini quota group A (project A: one or more authorized keys)
   +-- Gemini quota group B (project B, only if legitimately provisioned/allowed)
   +-- DeepSeek low-cost text/code/reasoning fallback
   +-- other explicitly configured fallback
```

**A quota group is a project/model capacity bucket, not an API key.** Multiple keys may help credential rotation/maintenance, but they do not create more per-project quota.

## Selection algorithm
1. Determine required capabilities: text/code/reasoning/image/audio/video/tools/schema/streaming.
2. Exclude providers/models that cannot preserve the contract.
3. Exclude privacy-ineligible tiers.
4. For Gemini, score healthy quota groups by cooldown state, estimated available budget, in-flight count, recent latency, and success rate.
5. Select the least-loaded healthy group.
6. Select an active credential inside that group.
7. Apply one bounded SDK/application retry policy—not nested retry storms.
8. On final retryable failure, fail over only to a compatible provider/model.
9. If no compatible provider exists, return an explicit degraded/unavailable product state.

## Failure classification
- **401**: credential invalid → quarantine credential; do not spray retries.
- **403**: permission/project/policy → quarantine and investigate; key rotation within the same bad project may not help.
- **404 model/resource**: refresh model/capability configuration; do not keep retrying an obsolete model.
- **429 short rate limit**: cooldown the project/model quota group; honor retry hints.
- **429 daily quota**: mark the quota group exhausted until reset; choose another legitimate eligible group/provider or degrade.
- **500/503/504/timeout**: bounded exponential backoff + jitter, then circuit-break/fallback.

## Retry budget
A request should have one owner for retry policy. If the SDK already retries, do not wrap it in multiple gateway/application retry loops without calculating the combined maximum.

Side effects triggered by model tool calls must be idempotent before whole-turn retry/failover.

## Cache/cost efficiency
- Put stable common instructions/context at the beginning when provider caching rewards common prefixes.
- Track cache-hit usage fields when the provider exposes them.
- Deduplicate identical in-flight requests when safe.
- Cache deterministic/low-temperature application results only when product semantics allow it.
- Prefer a fast/cheap eligible model for routine tasks and escalate model quality only when the task requires it.

DeepSeek's API supports automatic context caching and exposes cache-hit/miss token accounting; this makes it a useful low-cost fallback for compatible text/code/reasoning workloads. Do not route multimodal/tool contracts to a fallback that cannot preserve them.

## Secrets and logs
Log only safe routing metadata by default:
- request id;
- provider/model;
- quota-group id (not key);
- status/error class;
- latency;
- token/cache usage;
- fallback count.

Do not log raw API keys. Avoid raw prompts/responses by default, especially for sensitive product data.

## Example credential-group configuration
Keep keys in environment/secret management, not this repository:

```json
{
  "id": "gemini-project-a",
  "project_id_env": "GEMINI_PROJECT_ID_A",
  "key_envs": ["GEMINI_API_KEY_A1", "GEMINI_API_KEY_A2"],
  "tier": "free"
}
```

Only create multiple projects/credential groups when legitimately provisioned for your workloads and permitted by provider terms. Do not create them solely to bypass limits.

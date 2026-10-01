# Optional External Capabilities

The harness must work without these. Integrate only when they reduce real product risk or effort.

## UI UX Pro Max
Use as optional searchable design intelligence. Keep its dataset external/updatable; reconcile suggestions with product evidence and accessibility.

## Tencent BrowserSkill
Useful when verification must reuse a real logged-in Chrome/Edge session. Prefer it for authenticated acceptance flows that local Playwright cannot reproduce cheaply. Treat browser access as privileged.

## Playwright / Anthropic webapp-testing pattern
Project-native Playwright remains the default deterministic browser verification path. The key pattern is reconnaissance → action → screenshot/console/network evidence.

## Gemini Balance
Useful research for multi-key status monitoring, retries, disable/recovery, and Gemini/OpenAI-format proxying. Its repository license is CC BY-NC; this harness does not vendor its code.

## LiteLLM
A mature optional multi-provider gateway with unified APIs, load balancing, tracking, and guardrails. Consider when centralized gateway operations are actually needed.

## New API (QuantumNous)
Useful Chinese ecosystem reference for weighted channels, retry, rate limiting, format conversion, and multi-provider management. It is AGPL-3.0; this harness only studies patterns and does not vendor code.

## CLIProxyAPI
Useful research for protocol adaptation and provider/account routing. Do not use account/key pooling to bypass provider terms; official APIs and lawful credentials remain the default.

## DeepSeek ecosystem
DeepSeek's agent guides highlight direct provider integration, cache-first loops, flash-first cost control, tool-call repair, sandboxing, Skills/Hooks, and provider switching. Use DeepSeek as a cost-effective compatible fallback, not as an automatic substitute for unsupported modalities.

## Browser-use / Vibetest
Useful inspiration for adversarial website QA and broken-link/UI/accessibility discovery. The v5 baseline stays single-agent and deterministic; multiple browser agents are optional, not required.

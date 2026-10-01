# Research Sources Used for v5

Patterns were studied and reimplemented independently; third-party code is not vendored.

- Google Gemini API rate-limit, error, pricing, caching, and Google GenAI SDK documentation.
- `googleapis/js-genai` — current JavaScript/TypeScript SDK and retry/error behavior.
- `snailyp/gemini-balance` — multi-key monitoring, retries, disable/recovery (CC BY-NC 4.0; no code copied).
- `BerriAI/litellm` — centralized multi-provider gateway/load-balancing patterns.
- `QuantumNous/new-api` — weighted channels, retry/rate limiting, protocol conversion (AGPL-3.0; no code copied).
- `router-for-me/CLIProxyAPI` — provider/protocol routing patterns; research only.
- DeepSeek API documentation — error handling, account-level concurrency, context-cache telemetry, OpenAI/Anthropic-compatible interfaces.
- `deepseek-ai/awesome-deepseek-agent` — Reasonix/DeepSeek-TUI integration patterns.
- `Tencent/BrowserSkill` — real logged-in browser bridge and deterministic browser eval concepts.
- `anthropics/skills` webapp-testing — Playwright reconnaissance/action/screenshot/log pattern.
- `browser-use/vibetest-use` — vibe-coded web QA inspiration.
- Existing v4 sources: Superpowers, Claude Security, Better Harness, UI UX Pro Max, DeepCode.

## ECC (affaan-m/ECC) — reviewed 2026-09-06

MIT-licensed agent-harness project used as a research source for v5.2 mechanisms. We did not import its large agent/skill catalog. We reimplemented selected ideas in a smaller Codex-first form: manifest/ownership-based install lifecycle, cross-harness canonical/adapted surfaces, provenance-safe project-scoped learning, hook/loop budgeting principles, harness self-security, and exact packed-artifact validation. Upstream reference: https://github.com/affaan-m/ECC

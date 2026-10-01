# v5.5.10 source review - 2026-09-27

## Adopted mechanism

- LiteLLM issue #41344, opened 2026-09-16, documents a zero-cost requested model whose paid fallback executes after the initial budget gate and can therefore bill beyond the configured budget. The issue identifies the crucial boundary: re-evaluate budget against the actual fallback target immediately before execution, rather than blocking the free primary at initial auth. Source: https://github.com/BerriAI/litellm/issues/41344 . LiteLLM repository license: MIT. No LiteLLM implementation code is copied or vendored.

## Reviewed but not adopted as new code

- LiteLLM issue #40405 reports repeated retries against a known-dead primary before fallback. v5.5.9 already has bounded attempts/circuit breaker semantics; v5.5.10 only makes half-open and actual-target failure attribution explicit in machine policy. Source: https://github.com/BerriAI/litellm/issues/40405 .
- LiteLLM issue #39655 reports malformed `context_window_fallbacks` accepted until runtime. v5.5.10 generalizes the lesson into fail-fast fallback-graph validation rather than copying provider-specific parsing code. Source: https://github.com/BerriAI/litellm/issues/39655 .
- OpenAI Codex issue #47433 (2026-09-23) reports early sandbox denial missing from JSON command-execution events. Relevant to future execution-provenance work, but no Harness change here because v5.5.10 is intentionally scoped to provider routing. Source: https://github.com/openai/codex/issues/47433 . Codex license: Apache-2.0.

## UI/UX scan

Recent ui-ux-pro-max reports continue to show that indiscriminate design-skill application can regress an established design and that packaging/portability must be verified end-to-end. No UI Skill is modified in this release because there is no new paired live evidence/waiver justifying a canonical behavior change. Sources: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/446 and https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/issues/454 .

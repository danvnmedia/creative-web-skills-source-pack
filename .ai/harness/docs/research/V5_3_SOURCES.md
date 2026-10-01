# v5.3 Research Sources and What Was Reimplemented

This file records provenance for ideas, not copied implementation.

## Public sources reviewed

- `adewale/skill-eval-harness` (MIT): paired with/without-Skill causal lift, positive/negative trigger cases, answer-key-safe preparation, repeated runs, deterministic graders, token/cost telemetry, ablations.
- `SUNRNEHUI/agent-harness` (MIT): Native/Portable/Audited execution depth, progress circuit breaker, bounded durable context, verified acceptance.
- `AMAP-ML/LongHorizon-Harness` (MIT): fresh-context rounds and the rule that rejected executor results remain evidence rather than trusted progress.
- `ruvnet/metaharness` (MIT): deterministic repo analysis with explicit inferred trust, host adapters, measurable self-improvement, release provenance.
- `agentplugins/agent-plugins-spec` v1.0.0: portable `plugin.json` + fixed `skills/`/`mcp.json` discovery and plugin-root path containment. The Product Harness uses only the public format requirements for an optional skills-only export; host policy remains separate.
- `mrgoonie/claudekit-skills` / ClaudeKit public materials: progressive disclosure/context management and reusable Skill packaging patterns. No proprietary AgentKit content is bundled.

## Local design decisions

- Keep 13 canonical Skills; do not import external skill catalogs.
- Reimplement mechanisms in small dependency-free Python scripts.
- Do not claim autonomous Skill activation when the local agent runtime does not expose trustworthy attribution.
- Do not weaken product-quality gates merely because the execution profile is `native`.
- Treat inferred repo commands/URLs as non-executable until confirmed.

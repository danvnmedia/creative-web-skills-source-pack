# Skills Architecture v5

Skills are progressive capability packs. `AGENTS.md` stays general; task-specific methods load only when needed.

## Included Skills
- product-discovery
- codebase-recon
- feature-build
- systematic-debugging
- ui-ux-design
- runtime-verification
- security-hardening
- performance-reliability
- ai-provider-routing
- ai-integration-verification
- code-simplification
- release-acceptance
- harness-improvement

Each Skill has an actual `.agents/skills/<name>/SKILL.md` in the package. `validate_harness.py` fails if one is missing or malformed.

Detailed volatile material stays in `docs/` so the core Skill remains compact.

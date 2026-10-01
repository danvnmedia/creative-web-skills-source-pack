# Cross-Harness Surface Ownership

## Principle

Share policy, not assumptions about runtime features.

`AGENTS.md`, `.ai/`, and `.agents/` are canonical. `GEMINI.md`, `CLAUDE.md`, and `ANTIGRAVITY.md` are adapters that explain how to preserve the same contract when a harness exposes different hooks, browser tooling, MCP support, sandboxing, or agent delegation.

## Rules

1. Keep one canonical Skill copy under `.agents/skills/`.
2. Do not fork Skill bodies per harness unless an actual incompatible execution surface requires it.
3. Adapter docs must reference canonical task/quality policy rather than restating it in full.
4. Never claim feature parity from another harness.
5. Run `surface_drift.py` after editing adapters, rules, workflows, or Skill topology.
6. Antigravity is a first-class adapter and must remain represented in the surface contract.

## Verification

```bash
python .ai/scripts/surface_drift.py
```

For a harness-modification task, record this as `surface-drift` evidence.

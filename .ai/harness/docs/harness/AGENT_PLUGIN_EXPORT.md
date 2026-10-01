# Optional Agent Plugins v1 Export

The internal canonical Skill source remains `.agents/skills/`.

v5.3 can export that Skill surface as a **skills-only Agent Plugins v1 package** without moving or duplicating the canonical source inside the repository:

```bash
python .ai/scripts/export_agent_plugin.py --out /tmp/codex-product-harness-skills.zip
```

The export contains:

```text
plugin.json
skills/<skill-name>/SKILL.md
```

This export intentionally does **not** claim portability for host-specific install ownership, permissions, sandboxing, hooks, task/evidence policy, or production acceptance. Those remain the responsibility of each host adapter and the full Product Harness.

The exporter checks path containment, 13-Skill completeness, and POSIX ZIP separators.

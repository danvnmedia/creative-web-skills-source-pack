# Migration from Codex-First Product OS v3 to Codex Product Harness v4

v4 keeps v3's Codex-first, session-proof, quality-gate philosophy and adds an explicit harness layer.

## What changes
- `AGENTS.md` becomes a compact operating constitution with guide/sensor thinking.
- `.agents/skills/` adds just-in-time capability playbooks.
- `.ai/scripts/` adds deterministic evidence, workspace fingerprint, risk, resume, and harness-health utilities.
- Fresh evidence is tied to the current workspace fingerprint rather than conversational confidence.
- Debugging requires root-cause investigation before patching.
- Security separates candidate findings from verified findings.
- UI work adds design direction + rendered screenshot critique, with optional `ui-ux-pro-max` intelligence.
- Repeated agent mistakes trigger harness improvement rather than ever-longer prompts.
- Architectural principles should become executable structural tests where practical.

## Recommended migration
1. Keep project-specific values from the existing `.ai/PROJECT.md`, `.ai/COMMANDS.yaml`, task files, decisions, and approved product docs.
2. Replace the generic v3 runtime files with v4 equivalents.
3. Run `python .ai/scripts/harness_doctor.py`.
4. Fill missing command mappings before relying on automatic verification.
5. Run a real feature/bug through the new Skills and inspect whether evidence capture reduces ambiguity.
6. Add project-specific invariants only after observing recurring drift.

Do not overwrite product truth with template defaults during migration.

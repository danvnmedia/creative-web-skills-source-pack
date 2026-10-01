# Skill Security Gate

v5.4.4 adds a deterministic, fail-closed gate for Agent Skill files, directories, and ZIP archives before install, import, activation, or promotion.

## Contract

```bash
python .ai/scripts/skill_security_gate.py --target <skill-or-bundle> --fail-on review
```

The gate never executes code from the scanned target. It records an exact bundle SHA-256 and truthfully reports `scan_mode=deterministic-static`, `semantic_analysis=not_run`, `llm_used=false`, and `full_semantic_clean=false`.

The gate layers Skill-specific checks on top of the existing v5.4.1 quarantine rules:

- archive traversal, symlinks, file/member/byte ceilings, path depth, and compression-ratio ceilings;
- prompt/instruction override, credential material, exfiltration/destructive patterns, hidden Unicode, and encoded payloads;
- `SKILL.md` presence/frontmatter and duplicate Skill names;
- suspiciously broad trigger descriptions;
- unpinned `npx`, `pip install`, or `git clone` execution sources.

Resource-limit exhaustion is a block, not an incomplete clean result.

## Exact finding baselines

An optional baseline may contain `accepted_fingerprints`, but each fingerprint includes the rule, severity, path, detail class, and exact file SHA-256. Changing the affected file invalidates the old baseline even when the same rule still fires.

A baseline is an explicit risk decision, not proof the Skill is safe. Deterministic block findings remain visible in the report; semantic or external scanners may add findings but may not downgrade a deterministic critical result.

## Installation

`INSTALL_HARNESS.py` runs the gate against the canonical `.agents/skills` payload before it builds or applies an installation plan. Release packaging also runs both the historical quarantine scanner and this Skill-specific gate.

## v5.5.4 completeness rule

Opaque executable/compiled payloads and Python AST parse failures are completeness failures, not merely suppressible findings. An exact finding baseline may acknowledge a known finding but cannot convert `analysis_status=partial` into PASS. The gate adds bounded AST resolution for direct and statically reconstructed reflective Python execution while remaining a non-executing static sensor.

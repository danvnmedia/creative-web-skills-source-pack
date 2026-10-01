# Migration: v5.4.3 to v5.4.4

v5.4.4 is an additive supply-chain and context-boundary hardening release. The canonical baseline remains v5.3.0 and all 13 canonical `SKILL.md` files remain byte-identical to v5.3.0.

## Added

- `.ai/SKILL_SECURITY_POLICY.json`
- `.ai/scripts/skill_security_gate.py`
- `docs/harness/SKILL_SECURITY_GATE.md`
- `.ai/COMPACTION_POLICY.json`
- `.ai/scripts/checkpoint_reverify.py`
- `docs/harness/COMPACTION_TRUTH_BARRIER.md`
- `.ai/scripts/v544_regression_test.py`

## Behavior changes

`INSTALL_HARNESS.py` now performs a deterministic static security check of the exact canonical Skill payload before planning or mutation. It still uses the v5.4.3 collision-safe plan/digest/CAS/rollback installer and never takes ownership of generic project root files.

New verified checkpoints are schema 2 and include evidence lineage plus explicit claim status. Existing v5.3-v5.4.3 checkpoints remain readable when their original fresh passing evidence is still valid.

Portable/audited work should run `checkpoint_reverify.py` after compaction/context refresh before treating durable progress as current truth.

## Unchanged

Adaptive profiles, repo trust labels, candidate/source fingerprint rules, runtime-state exclusions, causal Skill activation semantics, Agent Plugins v1 export, Antigravity adapter, content-pinned waivers, deterministic control decisions, MCP surface pinning, browser lease, collision-safe installation, source-vs-installed validation, and exact-artifact release acceptance remain intact.

# v5.4.4 Public Mechanism Notes

Canonical baseline: Codex Product Harness v5.3.0. These notes capture public mechanisms only; no proprietary paid content is copied.

## NVIDIA SkillSpector

Source: https://github.com/NVIDIA/SkillSpector and public releases. Latest release observed during the v5.4.4 research run: v2.11.2, released 2026-09-10; Apache-2.0 repository.

Mechanisms distilled: pre-install Agent Skill scanning, bounded workflow/resource ceilings, supply-chain inspection, explicit incomplete/partial analysis semantics, and regression-heavy release validation. Harness implementation remains dependency-free and does not vendor SkillSpector code.

## Recent low-star/community Skill scanners

Sources observed in the 30-90 day hunt include `syntax-syndicate/agent-skill-scanner`, `rrrrrredy/skill-security-guard`, and `HTS-Sleeping-Place/skills-scanner`. Useful common mechanisms: deterministic static rules before optional judges, safe ZIP handling, broad agent-surface discovery, drift/baseline concepts, and truthful best-effort limitations. These sources are references for mechanism comparison, not dependencies.

## DeepSeek Harness compaction work

Source: https://github.com/deepseek-ai/deepseek-harness public compaction notes and docs, including implemented 2026-07 compaction capability/pressure/manual-compaction work and September 2026 crash/recovery discussions.

Mechanisms distilled: compaction as a bounded durable transaction, explicit start/end lifecycle, replayable failure state, preserved provider errors when compaction cannot prove progress, and source-event lineage. v5.4.4 applies the smallest single-primary-agent control: summaries may only reference already-verified progress and must be revalidated after a boundary.

## Senpi coding-agent compaction changes

Source observed 2026-09-10: https://github.com/code-yeongyu/senpi public compaction change notes.

Mechanism retained for future evaluation: deterministic resume slicing for restored sessions that are already over the context window, with bounded carry-forward of prior checkpoint summaries. Not adopted in v5.4.4 because model/provider context-window management belongs to the host runtime; the Harness only owns truth-preserving durable progress.

Release level: v5.4.4 hardening, not v6. No new multi-agent orchestration was introduced.

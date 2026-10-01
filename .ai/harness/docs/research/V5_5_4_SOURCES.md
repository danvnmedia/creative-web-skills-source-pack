# v5.5.4 research sources and decisions

Research date: 2026-09-20. No third-party implementation code was vendored.

## Adopted: static-analysis coverage truth

### NVIDIA/SkillSpector

- Repository: https://github.com/NVIDIA/SkillSpector
- Observed repository push: 2026-09-18; Apache-2.0 repository license.
- Public issue #479, opened 2026-09-02 and still open when reviewed: a dynamically resolved builtin (`getattr(builtins, ''.join(['e','x','e','c']))`) can downgrade/miss the direct `exec` signal. The local Harness reimplements only the small mechanism: bounded AST constant folding + sink resolution, with no copied implementation.
- Public issue #356, opened 2026-08-09 and closed 2026-08-12: executable Python bytecode hidden under `__pycache__` demonstrated why skipped executable content must not be interpreted as a clean scan. The Harness applies the coverage principle generically to opaque executable/compiled artifacts.
- Expected impact: no model tokens; small deterministic AST/magic-check CPU cost only during security scans. Measured release/runtime impact is recorded in acceptance evidence, not inferred from upstream results.

## Reviewed, not promoted

### tommasocerruti/eal-bench

- Repository created 2026-07-20 and active in September 2026; no license declared in GitHub repository metadata when reviewed.
- Endogenous Authorization Laundering is directly relevant to persistent memory and stale authority. The Harness already preserves failed/rejected evidence and requires verified progress, but it lacks a trustworthy cross-host authority-origin sensor that would justify adding an authorization ledger in this release.
- Decision: research lead only. Do not copy implementation or claim authority-laundering resistance.

### QoderAI/better-harness

- Active 2026-09-18. Recent work aligned disabled app UI/static serving with the same app-enablement predicate used by API/proxy routing.
- Decision: useful app-host boundary pattern, but no concrete gap in the current skills-only plugin / product Harness surfaces; not adopted.

Other newly surfaced agent-harness/security/browser repositories were compared against the current baseline. Catalog-heavy orchestration, duplicate mechanisms, and mechanisms without a concrete measured/truth gap were rejected for this release.

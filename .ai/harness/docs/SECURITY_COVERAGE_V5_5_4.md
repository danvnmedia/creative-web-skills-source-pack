# v5.5.4 Security Coverage Truth

Codex Product Harness v5.5.4 is an additive security-correctness release. Canonical compatibility and quality baseline remains **v5.3.0**; implementation parent is **v5.5.3**. All 13 canonical `SKILL.md` files remain byte-identical to the pinned v5.3 baseline.

## Problem closed

The v5.5.3 Skill/quarantine gates truthfully distinguished complete versus partial analysis for resource exhaustion, but two input classes could still produce an over-strong static-clean impression:

1. executable/compiled payloads that deterministic UTF-8 text/AST rules cannot inspect, including Python bytecode and common native/JVM/WASM/Node artifacts; and
2. Python execution sinks reconstructed through bounded reflection, such as assigning `getattr(builtins, ''.join(['e','x','e','c']))` and invoking the resulting callable.

A static scanner must not equate "no matching text rule" with "code inspected". v5.5.4 makes coverage itself evidence.

## Controls

### Opaque executable coverage

`.ai/scripts/quarantine_scan.py` detects common executable/compiled suffixes and selected executable magic. `opaque-executable-artifact` is both a blocking finding and an **analysis-incomplete** reason. The same coverage is used by `.ai/scripts/skill_security_gate.py`.

This does not claim that every binary format is recognizable. It establishes the stricter rule: when the gate knows executable bytes are opaque to its analyzers, it cannot report complete static analysis.

### Python AST sink resolution

For `.py` files, deterministic AST analysis resolves:

- direct `exec`, `eval`, `compile`;
- imports/aliases for selected standard-library runtime execution surfaces;
- bounded `getattr(module, <statically reconstructable string>)`, including constant concatenation and constant `str.join`;
- assignment aliases before invocation.

Direct or statically reconstructed `exec`/`eval` is blocking. Selected subprocess/runtime-loader surfaces are review-level. If Python parsing fails, `python-ast-incomplete` makes the analysis partial.

The implementation intentionally does **not** execute target code, evaluate arbitrary expressions, import target modules, decompile bytecode, or claim semantic completeness. Dynamic names not deterministically reconstructable remain outside this sensor and require stronger analysis/runtime containment where policy calls for it.

## Truth boundaries

- `analysis_status=complete` means only that the requested deterministic analyzers completed over supported content; it does not mean the package is safe in all runtimes.
- `analysis_status=partial` cannot be baseline-suppressed into PASS.
- Static finding baselines remain exact-content/fingerprint scoped.
- No fixture/mock result counts as live Skill activation, causal lift, host sandbox acceptance, or production acceptance.
- No canonical Skill changed, so `skill_modification=false` and no Skill live-eval waiver is needed for this release.

## Release regression

`.ai/scripts/v554_regression_test.py` covers direct execution, reflective builtins execution using constant construction, aliased runtime sinks, false-positive resistance for unimported module names, AST parse incompleteness, `.pyc` opacity, renamed ELF magic, end-to-end Skill gate status, canonical Skill hashes, v5.3 profile/Skill gates, and runtime-state exclusions.

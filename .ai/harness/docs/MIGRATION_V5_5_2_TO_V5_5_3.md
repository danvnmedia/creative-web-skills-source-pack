# Migration: v5.5.2 to v5.5.3

v5.5.3 is an additive truth/completeness release. Canonical baseline remains v5.3.0 and all 13 canonical `SKILL.md` files remain byte-identical to that baseline.

## What changes

1. Harness and Skill security scans now expose `analysis_status` and fail closed when required static analysis is incomplete. Resource-limit truncation is derived from raw findings before baselines, so accepting a known finding cannot turn unscanned bytes into a clean scan.
2. Release regression execution is discovered from `.ai/scripts/*_regression_test.py`; adding a deterministic regression no longer requires editing a manual release allowlist. Live/external E2E remains separate and never counts as deterministic PASS.
3. Full-catalog Skill routing has a 39-case contract: for each of 13 Skills, one full-catalog positive, one full-catalog negative, and one target-excluded baseline. Deterministic matrix validation is not autonomous activation proof.
4. `host_surface_contract.py` can compare a pinned machine-readable host capability snapshot with an explicit support map. Newly observed unclassified host keys fail; stale mappings are reported. This does not claim host parity or fetch upstream surfaces automatically.

## Upgrade safely

Extract the release outside the product repository. Run `python INSTALL_HARNESS.py --target <project>` first and review the plan. Apply only with the exact fresh `plan_digest` shown by the installer. Existing project-owned root files and modified mutable runtime seeds remain protected by the ownership-aware installer.

No automatic global plugin/MCP installation, host configuration change, deployment, credential access, or project migration is performed by this release.

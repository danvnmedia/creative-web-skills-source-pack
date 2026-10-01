# Migration: v5.4.2 to v5.4.3

v5.4.3 is an additive installation-boundary hardening release. Canonical baseline remains v5.3.0 and all 13 `SKILL.md` files remain byte-identical to the v5.3 baseline.

Main changes:

1. Collision-safe installer becomes plan-first; apply requires the current `plan_digest` and compare-and-swap checks.
2. Generic root release metadata and `docs/**` / `templates/**` are relocated to `.ai/harness/**` instead of being copied over product paths.
3. Root agent entrypoints and immutable-Skill doc compatibility paths use managed pointer blocks that preserve project content outside markers.
4. Install state schema 2 records whole-file vs managed-block ownership baselines.
5. Source distributions are marked by `.ai/SOURCE_DISTRIBUTION.json`; that marker is never installed into a product repository.
6. `self_test.py` distinguishes source and installed contexts. Installed tests validate Harness-owned state only; application `.git`, `node_modules`, config and build output are not package residue.
7. `package_release.py` and `verify_package.py` refuse installed product repositories instead of packaging or diagnosing them as Harness source trees.
8. Harness version lookup uses `.ai/harness/VERSION` in installed mode, preventing application `VERSION` from contaminating Agent Plugin export metadata.

Upgrade using the new release installer. The first run is read-only; use its exact digest for the apply run.

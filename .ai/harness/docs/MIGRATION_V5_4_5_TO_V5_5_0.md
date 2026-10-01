# Migration: v5.4.5 -> v5.5.0

v5.5.0 is an additive Evidence Architecture and operator-reliability release on the canonical v5.3.0 contract. The 13 canonical Skills remain byte-identical.

Key changes:

1. Canonical task identity: paths are locators; evidence identity is always `task.id`.
2. Atomic per-event evidence files and collision-safe contained log paths.
3. Separate product-source, task-contract and lifecycle-state digests.
4. Task schema v6 and validated task transitions; schema v5 remains readable during migration.
5. Early candidate preflight; non-Git work may use explicit `--snapshot`, which is `LOCAL_SNAPSHOT_ACCEPTED` only and can never satisfy production acceptance.
6. Source-vs-installed command routing via `harness.py`; source validators refuse installed context explicitly.
7. Windows-safe byte restoration, temp fallback/leases, ACL handling and cleanup.
8. Quarantine findings distinguish rule definitions/test fixtures/documentation from executable occurrences.
9. Browser capability reporting separates project reproducibility from host/browser-plugin availability.

Do not copy the source ZIP over a product root. Use the collision-safe plan/apply installer and verify the installed runtime with `python .ai/scripts/harness.py verify ...`.

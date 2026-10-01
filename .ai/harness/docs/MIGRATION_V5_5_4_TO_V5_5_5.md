# Migration 5.5.4 -> 5.5.5

Use the source installer in plan/digest mode, not a manual overlay. Canonical
baseline remains 5.3.0; no Skill bodies or runtime state schema are replaced.
Existing product README/VERSION/CHANGELOG/LICENSE/docs, custom agent blocks,
mutable state, checkpoints and evidence must retain their byte identity.

New additive gates: regression-environment-contract, git-machine-output-contract,
newline-structure-contract. The full deterministic-e2e-complete remains required
for Harness changes and must be run from verified SOURCE, not from an installed
product repository. It does not become optional merely because installed mode
refuses the wrong invocation. Capture its exact-source/environment evidence.

The installer already refuses newer/different lineage and ownership conflicts;
this patch does not override that behavior or downgrade a separate 5.6 branch.
Source metadata remains namespaced when installed. No global Git changes.

See WINDOWS_EXECUTION_V5_5_5.md for scratch selection and evidence limitations.

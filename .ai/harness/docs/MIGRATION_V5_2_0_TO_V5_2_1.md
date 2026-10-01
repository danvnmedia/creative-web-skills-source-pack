# Migrating from v5.2.0 to v5.2.1

v5.2.1 fixes the install/overlay recovery gap discovered in a real Codex project: a manual copy could leave `.ai/` present while `.agents/` was missing, causing `adopt`, `surface_drift`, and `validate_harness` to fail with no pre-adoption repair path.

## Preferred upgrade

Extract the v5.2.1 release to a temporary directory outside the project, then run:

```bash
python INSTALL_HARNESS.py --target /path/to/project
```

The installer uses the existing install-state ledger or previous harness manifest as the ownership baseline. It copies missing files, upgrades files that still match the prior managed hash, and preserves conflicting/user-modified files unless `--force-conflicts` is explicitly requested.

## Recovery after a partial manual overlay

If the v5.2.1 `.ai/scripts/` files and manifest are already present in the target project but `.agents/` or another managed path is missing, run:

```bash
python .ai/scripts/harness_ownership.py bootstrap --source /path/to/Codex_Product_Harness_v5.2.1.zip
python .ai/scripts/harness_ownership.py adopt
```

`bootstrap` restores missing files but does not overwrite mismatched existing files by default.

## Verify

```bash
python .ai/scripts/harness_doctor.py
python .ai/scripts/surface_drift.py
python .ai/scripts/harness_security.py
python .ai/scripts/validate_harness.py
python .ai/scripts/self_test.py
```

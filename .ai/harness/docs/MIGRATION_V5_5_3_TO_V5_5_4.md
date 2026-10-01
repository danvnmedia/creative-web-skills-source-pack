# Migration: v5.5.3 to v5.5.4

v5.5.4 is additive. Canonical baseline remains v5.3.0 and the 13 canonical Skills do not change.

## What changes

The pre-install Skill/quarantine security gates are stricter about analysis coverage. A package containing opaque executable/compiled payloads can now be `partial`/blocked even if v5.5.3 found no textual rule match. Python source also receives bounded AST sink analysis, including statically reconstructable reflective `exec`/`eval`.

This is intentionally fail-closed. If a trusted package legitimately contains compiled artifacts, do not create a baseline merely to turn partial analysis into PASS; use an appropriate stronger review/verification path or keep it out of the trusted Skill bundle.

## Safe upgrade

Extract the v5.5.4 release outside the product repository and run the installer in plan-only mode first:

```bash
python INSTALL_HARNESS.py --target /path/to/project
```

Review the exact `plan_digest`, then apply that observed plan:

```bash
python INSTALL_HARNESS.py --target /path/to/project --apply --confirm <plan_digest>
```

The ownership-aware installer preserves project-owned generic roots and mutable Harness runtime state. Do not copy the release tree wholesale into the project root.

## Verification

After install/upgrade, run the installed-context self-test and normal task verification. Native Windows junction behavior remains a native-platform check; Linux fixtures must not be reported as equivalent proof.

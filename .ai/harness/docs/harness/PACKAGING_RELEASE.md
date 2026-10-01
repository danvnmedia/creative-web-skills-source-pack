# Packaging and Release

A filename is not release identity. v5.5.1 preserves the v5.4.3 separation of release-source validation from installed-runtime validation.

Run release packaging only from an extracted source distribution containing `.ai/SOURCE_DISTRIBUTION.json` and no `.ai/HARNESS_INSTALL_STATE.json`:

```bash
python .ai/scripts/package_release.py --out /path/to/Codex_Product_Harness_v5.5.1.zip
```

The packager builds SPDX-2.3 SBOM and the ownership manifest; validates source structure, surfaces, security, quarantine, Skill security gate, compaction-truth contract and canonical v5.3 Skill hashes; runs focused v5.3/v5.4.1/v5.4.2/v5.4.3/v5.4.4/v5.5.0/v5.5.1 regressions plus self-test; writes portable ZIP paths; verifies the exact ZIP; re-extracts and verifies it again; creates the release witness; and verifies the witness.

Runtime state `.ai/REPO_MAP.json`, `.ai/HARNESS_INSTALL_STATE.json`, and `.ai/checkpoints/**` is excluded except checkpoint control documentation.

If `package_release.py` is invoked inside a product repository where the Harness is installed, it refuses before packaging. Use `verify_installation.py` / `self_test.py --context installed` there. Never weaken source residue rules merely because a product repository legitimately contains `.git`, `node_modules`, application config, or build output.

# Source Distribution vs Installed Runtime Boundary

Codex Product Harness has two distinct filesystem contexts. They must never be validated or packaged as if they were the same thing.

## Source distribution

An extracted release/source tree contains `.ai/SOURCE_DISTRIBUTION.json`, root release metadata (`README.md`, `VERSION`, `CHANGELOG.md`, `SBOM.spdx.json`), release docs, tests, and packaging tools. `verify_package.py`, `build_manifest.py`, `build_sbom.py`, and `package_release.py` operate on this boundary. Source/package residue rules remain strict: `.git`, `node_modules`, build output, caches, bytecode, backups, runtime checkpoints, and install state are not valid release payload.

`package_release.py` fails closed when install state is present or the source-distribution marker is absent. This prevents an installed product repository from being archived as if it were the Harness release.

## Installed runtime

A product repository contains its own files and may legitimately contain `.git`, `node_modules`, `package.json`, application `README.md`, application `VERSION`, project docs, build output, and other product-owned state. Those files are not Harness package residue.

A v5.4.3+ managed install is identified by `.ai/HARNESS_INSTALL_STATE.json` schema 2. Harness release metadata lives under `.ai/harness/**`; root generic project files are not claimed by Harness ownership. Root agent surfaces and the three immutable-Skill companion doc paths use marker-scoped pointer blocks so content outside the blocks remains project-owned.

`verify_installation.py` validates only whole files and managed blocks recorded in install state plus the canonical v5.3 Skill hash contract. `self_test.py` selects source or installed validation explicitly and never substitutes one for the other.

## Why this is a hard boundary

A release validator answers: “Would these bytes form a clean, exact Harness artifact?” An installed-runtime validator answers: “Is the Harness-owned subset inside this application still intact and safe?” Mixing those questions produces false residue failures and can also cause dangerous packaging of an application repository.

Do not relax source artifact rules to make installed-runtime tests pass. Fix the boundary instead.

# Collision-Safe Install and Ownership

v5.4.3 installs are plan-first and transactional. A package filename or path collision never proves ownership.

## Default workflow

From an extracted trusted Harness release:

```bash
python INSTALL_HARNESS.py --target /path/to/project
```

This is read-only and prints a `plan_digest`. Review conflicts and the action counts. Apply only the exact observed plan:

```bash
python INSTALL_HARNESS.py --target /path/to/project --apply --confirm <plan_digest>
```

Before every write the installer rechecks the observed target bytes. If a planned file or managed-block container changed, the digest becomes stale and apply is refused. Writes are staged with rollback metadata under `.ai/checkpoints/install-transactions/**`; raw backup bytes are deleted after a successful transaction.

## Project-protected roots

The installer never blindly owns application `README.md`, `VERSION`, `CHANGELOG.md`, `LICENSE*`, `docs/**`, `templates/**`, `START_HERE_PROMPT.md`, `SBOM.spdx.json`, or root `INSTALL_HARNESS.py`.

Harness release metadata and documentation are relocated under `.ai/harness/**`. Existing project content remains untouched.

Root `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `ANTIGRAVITY.md` receive only marker-scoped pointer blocks. The immutable v5.3 Skills reference three `docs/*.md` paths; those paths likewise receive tiny managed pointer blocks to the namespaced Harness docs. Existing content outside markers is preserved byte-for-byte.

## Ownership baseline

`.ai/HARNESS_INSTALL_STATE.json` schema 2 records each managed target as either:

- `whole_file`: current bytes may be automatically updated only when they still match the last managed hash;
- `managed_block`: only the exact marker block is Harness-owned; surrounding content is never part of Harness ownership.

An exact pre-existing file may be adopted for integrity checking but is not marked `created_by_harness`; uninstall therefore preserves it.

Local modification of a Harness-owned whole file or marker block creates a protected conflict. There is no silent force-overwrite path in the normal installer.

## Repair and uninstall

For v5.4.3+ state, `harness_ownership.py repair --source ...` uses the same plan/digest contract as installation. A new release's `INSTALL_HARNESS.py` remains the preferred upgrade path.

`harness_ownership.py uninstall` is dry-run by default. `--apply` removes only proven Harness-created whole files and unchanged managed blocks. Modified managed content is preserved and remains registered for review.

Legacy schema-v1 adopt/bootstrap flows remain available only as explicit historical recovery paths and are not the recommended v5.4.3 installation model.


## Runtime/project mutable seeds (v5.4.5)

Not every Harness-seeded file is immutable Harness code. The following are deliberately `mutable_seed` surfaces after installation: `.ai/PROJECT.md`, `.ai/STATE.json`, `.ai/COMMANDS.json`, `.ai/RESUME.md`, and `.ai/DECISIONS.md`.

The installer owns their initial seed but not every future byte. Verification reports divergence from the seed without treating it as immutable Harness tamper. Update/repair preserves modified mutable seeds; only pristine seeds may advance automatically. Immutable scripts, policies, canonical Skills, snapshots, and managed blocks remain hash-strict. Do not manually rebaseline mutable runtime hashes to make a self-test pass.

## v5.5 note
Ownership classes are unchanged: mutable seed divergence is preserved; v5.5 adds source/task/lifecycle evidence identities and does not turn runtime state back into immutable ownership.

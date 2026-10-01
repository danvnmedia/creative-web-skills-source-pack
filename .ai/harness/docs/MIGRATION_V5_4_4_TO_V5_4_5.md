# Migration: v5.4.4 -> v5.4.5

v5.4.5 fixes an ownership-model defect discovered in real project use: the collision-safe installer recorded some intentionally mutable runtime/project seed files as immutable whole-file Harness ownership. A legitimate `bootstrap_project.py --write` therefore changed `.ai/COMMANDS.json` and caused `verify_installation.py` to report Harness drift. The same defect applied to lifecycle surfaces such as `.ai/STATE.json` and human-maintained `.ai/PROJECT.md`, `.ai/RESUME.md`, and `.ai/DECISIONS.md`.

## New ownership class: `mutable_seed`

The installer now classifies exactly these five seeded surfaces as `mutable_seed`:

- `.ai/PROJECT.md`
- `.ai/STATE.json`
- `.ai/COMMANDS.json`
- `.ai/RESUME.md`
- `.ai/DECISIONS.md`

Harness installs their initial seed, but later runtime/project edits are expected. Verification reports seed divergence truthfully without treating it as immutable Harness tamper. Immutable controls, scripts, policies, canonical Skills, and managed blocks remain hash-strict.

## Update behavior

- pristine mutable seeds may advance to a newer seed;
- modified mutable seeds are `PRESERVE_MUTABLE` and are never overwritten automatically;
- unknown pre-existing paths remain `PROTECTED_CONFLICT`;
- schema-2 v5.4.3/v5.4.4 ownership records migrate to schema 3 without clobbering runtime changes;
- no manual ownership-hash rebaseline is required or recommended.

Manual rebaselining of runtime hashes is intentionally avoided because it can make customized runtime state look pristine and permit a future installer to overwrite it.

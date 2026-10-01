# Migrating from v5.1 to v5.2

## What changed

- Task schema 3 adds `traits.harness_modification`.
- Quality policy 3 adds `harness-security`, `surface-drift`, `package-contract`, and `harness-self-test` requirements for harness changes.
- Added cross-harness canonical/adapted surface ownership and a first-class Antigravity adapter.
- Added deterministic harness file manifest plus ownership-aware status, repair, and uninstall.
- Added project-scoped lesson candidates with confidence, evidence, provenance, and human-gated promotion.
- Added failure signatures and a loop guard for repeated identical verification failures.
- Added harness attack-surface security scanning.
- Release packaging now writes POSIX ZIP paths and verifies the exact archive after packaging.

## Upgrade steps

1. Overlay v5.2 onto the project root after reviewing the diff.
2. Copy any missing task-template fields for active tasks; existing task JSON remains readable.
3. Set `harness_modification=true` only when the task changes the harness/control plane itself.
4. Run:

```bash
python .ai/scripts/build_manifest.py
python .ai/scripts/harness_ownership.py adopt
python .ai/scripts/harness_doctor.py
python .ai/scripts/surface_drift.py
python .ai/scripts/harness_security.py
python .ai/scripts/validate_harness.py
python .ai/scripts/self_test.py
```

5. Commit the reviewed harness upgrade and `.ai/HARNESS_INSTALL_STATE.json` if your team wants ownership state shared; otherwise keep that generated state local according to repository policy.

## Do not

- promote one project lesson directly into a global Skill;
- duplicate canonical Skill bodies for each harness;
- delete files during uninstall based only on path names;
- assume Antigravity/Gemini/Claude/Codex runtime feature parity;
- repeat identical failing checks after the loop guard says stop.

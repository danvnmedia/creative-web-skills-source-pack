# Migrating from v5.0 to v5.1

## What changed

- Task schema 2 adds experience, state, claim, capacity, and release contracts.
- Quality policy 2 adds state recovery, capacity degradation, claim contract, and production critical-flow gates.
- Evidence recording is UTF-8 safe, detects unexpected workspace mutation, and supports ephemeral post-closure probes.
- Candidate evidence can survive closure-only metadata changes through a validated closure manifest.
- Browser runs can require fresh output and test durable attribute changes, reload recovery, overflow, and overlap.
- Workspace hygiene detects caches, temporary files, untracked environment files, and source dirt.

## Existing task migration

Existing task JSON remains readable. For active work:

1. copy missing fields from `.ai/TASK_TEMPLATE.json`;
2. set the three new traits accurately;
3. fill the relevant experience and state contracts;
4. add release identity only when `production_release=true`;
5. rerun fresh evidence because required checks may have expanded.

Do not set a new trait to false merely to avoid its required check. If a check genuinely cannot run, use a time-bounded waiver with owner, reason, risk, and expiry.

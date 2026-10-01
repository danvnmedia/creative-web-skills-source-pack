# Migration: v5.5.0 -> v5.5.1

v5.5.1 is an additive completion release on canonical v5.3.0. The 13 canonical Skills remain byte-identical.

## What changes

- Verification mappings move from hard-coded router heuristics into `.ai/CHECK_CATALOG.json`. Shared regression runners execute once and may satisfy multiple declared checks with catalog-digest-pinned evidence.
- Evidence gains `runtime_candidate_digest`; only runtime/deployment-sensitive checks are invalidated by candidate/deployment identity changes. Source-only build/test evidence still keys off product source + task contract.
- Browser capability reporting distinguishes a fresh host-receipt connected browser, project-local Playwright, owner-approved transient Playwright, and unavailable state. An environment declaration alone is not trusted receipt evidence.
- `HARNESS_TEMP_DIR` is accepted in addition to `HARNESS_TMP`; OS temp is used when writable and workspace `.ai/checkpoints/tmp` is the controlled fallback when it is denied.

## Compatibility

No v5.3 Skill file changes. Existing v5.5.0 evidence without runtime-candidate metadata remains readable; new runtime-bound evidence records the field. Existing direct scripts remain available; normal operator flow should use `python .ai/scripts/harness.py verify ...` or `verify_all.py`.

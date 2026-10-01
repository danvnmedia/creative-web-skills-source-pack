# Skill pack upgrade — 2026-09-30

## Changes

- Added `accessible-interaction-systems` for reusable component semantics, keyboard/touch parity, state feedback, and focused examples. Its boundary is component behavior; page-wide choreography remains with `motion-choreographer`.
- Tightened frontmatter descriptions of the six existing creative skills so the broad Studio, implementers, rebuild skill, and auditor have clearer triggers. No existing skill or example was removed or merged because their responsibilities are distinct.
- Added `motion-choreographer/references/modern-motion-support.md` with current scroll timeline, View Transition, spring, and reduced-motion support/fallback decisions.
- Added a root command surface (`package.json`) and local static server so Harness can map observed `dev`, `build`, `lint`, and `test` commands. This preserves the nested Asme package and its lockfile.
- Added `scripts/validate-skills.mjs` and 14 routing review cases. The validator checks seven skill entrypoints, metadata, descriptions, relative reference links, and fixture coverage. Repository validation now includes seven generated skill routes; CI runs the new skill check.
- Updated the hub, README, and showcase index for the seventh skill and reviewed external sources.
- Narrowed `.gitignore` for runtime transaction checkpoints, event streams, logs, browser captures, completion reports, and generated build output. Harness ownership state and review reports remain visible for Git review.

## Verification so far

- `npm.cmd run lint`: PASS — seven skill structures, metadata, links, and 14 routing review fixtures.
- `npm.cmd run test`: PASS — seven routes, four showcases, and local Pages links after build.
- `python .ai/scripts/skill_security_gate.py --target <each of seven skills> --fail-on block`: 0 blocks across seven static-only scans. Six return `pass`; `shader-web-art` returns `review` for two `network-client` findings in existing reference documents. Those files contain written examples and external resource references; the findings remain visible for manual review.
- Installed Harness ownership and surface drift: PASS after project-owned additions.

The bundled `skill-creator` quick validator could not start in this Python environment because PyYAML is absent (`ModuleNotFoundError: yaml`). The repository validator and Harness static security gate ran instead. The routing fixtures test catalog coverage, not autonomous skill activation; trusted host telemetry or paired evaluation would be needed for an activation claim.

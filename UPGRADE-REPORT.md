# Creative Web Skills Pack — Architecture Review

## Executive assessment

The pack has a strong specialist split, unusually good restraint around rendering choices, and clear IP, accessibility, mobile, and performance principles. Its main weakness was operational rather than conceptual: each skill described good practice, but the pack did not define how work and evidence move between skills, and all showcases were external references.

## Changes completed

1. Added a shared handoff packet to `creative-web-studio` covering thesis, scene state, rendering layers, motion ownership, budgets, variants, acceptance criteria, and unknowns.
2. Connected motion, 3D, shader, rebuild, and audit skills to that contract while preserving their specialist boundaries.
3. Added proof requirements for mobile, reduced motion, input alternatives, capability failure, framing, cleanup, and offscreen behavior.
4. Replaced vague performance guidance with adaptable planning ranges for frame time, DPR, draw calls, GPU texture memory, first-scene media, and initial JavaScript.
5. Added four first-party showcase sites that exercise the pack's own principles instead of linking only to external inspiration.
6. Added a GitHub Pages workflow that rebuilds the React showcase and publishes the complete showcase hub from `main`.

## Architecture scorecard

| Area | Before | After | Remaining opportunity |
|---|---:|---:|---|
| Skill discovery and boundaries | Strong | Strong | Add trigger evaluation fixtures |
| Creative specificity | Strong | Strong | Add more non-luxury and application examples |
| Cross-skill orchestration | Limited | Strong | Automate packet validation |
| Accessibility and mobile | Strong guidance | Testable guidance | Add automated axe checks |
| Performance | Good heuristics | Measurable defaults | Add Lighthouse/WebPageTest capture scripts |
| First-party proof | Missing | Four runnable demos | Publish captures and field results |
| Maintenance | Manual | Documented model | Add CI for links, frontmatter, and smoke tests |

## Recommended next investments

### P1 — Evaluation fixtures

Create 12–20 representative prompts with expected skill routing, required output fields, and anti-pattern assertions. This will test whether descriptions trigger the right skill and whether answers preserve the handoff contract.

### P1 — Automated showcase QA

Add Playwright checks for desktop/mobile screenshots, horizontal overflow, keyboard focus, reduced motion, WebGL fallback, and nonblank canvas pixels. Run the static auditor alongside these browser checks.

### P2 — Pack validator

Validate folder/name agreement, YAML frontmatter, required references, broken relative links, agent metadata, and duplicate or contradictory guidance in CI.

### P2 — Runtime evidence templates

Add a compact audit artifact format for device profile, route, viewport, network, measured values, screenshots, and residual risks. This would make comparisons across generated projects repeatable.

### P3 — Broader calibration

Add worked examples for public-interest services, dense operational tools, commerce, education, and low-bandwidth markets so “creative web” is not calibrated mainly against launch pages and portfolios.

# Motion Performance Auditor — Finding Examples

Use this file to calibrate evidence, severity, and fixes. Static findings are hypotheses until runtime measurement confirms impact.

## Example 1 — React state update every R3F frame

**Finding**

```tsx
useFrame((_, delta) => {
  setRotation((r) => r + delta)
})
```

**Why it matters**

This can drive React updates at render-loop frequency.

**Preferred direction**

Mutate an object/ref inside `useFrame` when the value is purely visual and does not need React reconciliation.

**Severity**

Usually P1/P2 depending on component tree and measured impact.

---

## Example 2 — Uncapped DPR

**Finding**

A full-screen canvas renders at raw device pixel ratio on high-density phones.

**Fix**

Use a capped/adaptive DPR and test visual quality against GPU/frame-time improvement.

**Validation**

Compare GPU/frame time, thermal behavior, and visual sharpness on a high-DPR phone.

---

## Example 3 — Layout read inside high-frequency pointer/RAF loop

**Finding**

`getBoundingClientRect()` is called for many items every animation frame.

**Fix**

Cache geometry and refresh on resize/layout changes; coordinate reads and writes; only measure continuously if actual layout changes continuously.

---

## Example 4 — ScrollTrigger lifecycle leak

**Finding**

A route mounts timelines/ScrollTriggers but never reverts/kills them on unmount.

**Symptoms**

Duplicate callbacks, stale triggers, increasing work after navigation.

**Fix**

Own animation setup in a lifecycle boundary (`gsap.context`, framework effect cleanup, or page-view teardown) and verify trigger count after repeated navigation.

---

## Example 5 — Overlong pinned scene

**Finding**

A two-sentence message consumes ~500vh of scrolling while the visual changes only once.

**Severity**

P2 usability/motion issue even if frame rate is perfect.

**Fix**

Reduce pin distance or replace with a normal section + short triggered transition. Performance auditing includes narrative efficiency.

---

## Example 6 — Heavy postprocessing on mobile

**Finding**

Full-resolution bloom + depth-of-field + SSAO run continuously over a mostly static hero.

**Fix order**

1. Remove passes that do not materially support the art direction.
2. Lower render scale/quality tier.
3. Pause/reduce when idle or offscreen.
4. Replace with baked/art-directed textures when visually equivalent.

---

## Example 7 — Missing reduced-motion design

**Finding**

The entire experience depends on large camera pushes and scrubbed parallax.

**Fix**

Create a deliberate alternate composition using cuts, opacity, stepped states, and static posters. Do not merely set all durations to zero if it breaks hierarchy.

---

## Example 8 — Sample audit summary

**Executive summary**

> The site is visually strong but spends too much continuous work on one hero canvas and duplicates scroll listeners after route changes. The biggest user-facing improvements are to cap DPR/adapt postprocessing, fix animation cleanup, and shorten the mobile pinned sequence.

**Prioritized findings**

- P1: duplicate ScrollTriggers after client-side navigation — confirmed by trigger count growth.
- P1: canvas remains active offscreen — confirmed by profiler/timeline.
- P2: uncapped DPR — source evidence; runtime impact expected, verify on high-density phone.
- P2: mobile pin duration causes excessive interaction cost.
- P3: several hover effects lack consistent focus-visible equivalents.

Separate **evidence**, **inference**, and **validation step** for every nontrivial finding.

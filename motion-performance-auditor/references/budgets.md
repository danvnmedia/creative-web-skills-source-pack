# Default Budgets

These are starting constraints, not universal laws.

## Experience metrics
- LCP <= 2.5s p75
- INP <= 200ms p75
- CLS <= 0.1 p75

## Runtime
- target 60 fps on capable desktop and 30 fps minimum on constrained supported devices
- treat repeated frame time above 16.7ms at a 60Hz target or above 33.3ms at a 30Hz target as a quality-tier signal
- keep main-thread tasks below 50ms where practical; investigate repeated long tasks in interaction paths
- pause continuous decorative work when hidden and reduce or stop it when offscreen

## 3D
- cap DPR; start with 1–1.5 on mobile and 1–2 on desktop, then adapt from evidence
- target fewer than 100 visible draw calls for a focused hero on mid-range mobile; justify higher counts with profiling
- keep first-scene GPU textures roughly below 32–64MB on mobile and 64–128MB on desktop as an initial planning range
- avoid full-resolution post-processing on constrained devices
- load only first-scene assets eagerly

## Media
- keep eagerly loaded first-scene media near or below 2MB on mobile and 4MB on desktop when the concept permits
- use responsive dimensions and modern formats; do not send a desktop source to a narrow viewport by default
- treat autoplay video, frame sequences, and GLB files as first-class budget items
- prefer poster-first and progressive/lazy loading

## JavaScript
- use 200KB gzip as a warning line for initial route JavaScript, not an automatic failure
- split 3D, editors, and below-fold creative effects from the initial interaction path
- avoid shipping authoring/debug tooling to production

## Reporting rule

Record the actual value, test profile, and source of each measurement. When a project intentionally exceeds a default, document what visitor value buys that cost and which lower quality tier protects constrained devices.

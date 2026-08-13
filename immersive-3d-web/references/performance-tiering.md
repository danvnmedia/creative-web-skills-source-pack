# 3D Performance Tiering

Create at least three tiers.

## Tier A — high capability
- capped DPR around 1.5–2 depending on workload
- full model LOD
- selected post-processing
- higher particle count
- quality shadows only if budget allows

## Tier B — typical laptop/mobile
- lower DPR
- reduced texture size/anisotropy
- fewer particles/lights
- simplified post-processing
- shorter camera sequences

## Tier C — constrained / reduced motion / no WebGL
- static poster or lightweight CSS/SVG alternative
- essential content remains in DOM
- optional click-to-enable 3D instead of autoplay

## Signals
Use measured frame time, viewport size, memory/feature signals when available, and user preference. Avoid simplistic “mobile = weak” assumptions.

## Targets
Prefer stable 60fps where realistic; a stable lower rate is better than wild frame-time spikes. Investigate draw calls, shader complexity, overdraw, texture memory, post-processing passes, and React churn.

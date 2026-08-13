# Creative Web Audit Checklist

## Loading
- LCP asset discoverable early
- hero video/3D does not block message
- fonts/images sized and preloaded only when justified
- heavy client code dynamically split where useful

## Main thread
- no frequent forced layout
- no frame-rate React state updates
- long tasks investigated
- scroll handlers passive/lightweight or replaced with better primitives

## Animation
- transform/opacity preferred for continuous motion
- timelines/listeners cleaned up
- one primary ticker/RAF strategy
- pin lengths justified
- reverse states correct

## WebGL
- DPR capped/adaptive
- render loop pauses/reduces offscreen
- textures/geometry/materials budgeted
- assets lazy-loaded
- post-processing tiered
- manual resources disposed

## Accessibility
- reduced motion
- keyboard/focus
- semantic fallback
- touch alternatives
- contrast/readability unaffected by motion

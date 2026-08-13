# Tool Selection Matrix

## Native first
Use CSS transforms, transitions, keyframes, clip-path/masks, SVG, IntersectionObserver, WAAPI, CSS scroll-driven animations, and View Transitions when they solve the problem cleanly.

## Motion for React
Best for React component animation, layout transitions, shared-layout continuity, gestures, spring/tween UI feedback, and concise scroll-linked effects. Prefer when animation state is tightly coupled to React UI.

## GSAP + ScrollTrigger
Best for precise multi-step timelines, advanced scrub/pin choreography, FLIP, SVG/text sequencing, cross-system orchestration, and creative-dev scenes requiring deterministic control.

## Lenis
Use only if smooth scrolling contributes materially. Keep anchors, keyboard behavior, touch momentum, history, and native expectations working. Avoid multiple smooth-scroll engines.

## Rive
Use for authored interactive vector animation driven by state machines/data binding. Good for branded controls, characters, diagrams, or interactive illustrations.

## Lottie / dotLottie
Use for authored vector/timeline motion when state-machine complexity is unnecessary. Favor smaller, controlled compositions and pause when offscreen.

## Spline
Use when a scene is authored in Spline or a visual 3D workflow is desired. Avoid multiple heavy embeds; export/self-host when workflow and licensing allow; treat it as real WebGL cost.

## PixiJS / Curtains / OGL
Use for GPU 2D image fields, particles, displacement, texture transitions, and DOM-aligned shader effects where full Three.js scene machinery is excessive.

## Three.js / React Three Fiber + Drei
Use for custom 3D worlds, models, camera choreography, post-processing, instancing, physics, or shader-heavy spatial experiences. In React projects prefer R3F when declarative scene composition and ecosystem helpers improve maintainability.

## Theatre.js
Use when designers/developers benefit from authored timelines and visual sequencing, especially for 3D camera/object animation.

## WebGPU
Use as progressive enhancement for workloads that genuinely benefit from modern GPU pipelines/compute. Capability-detect and provide a WebGL or non-GPU fallback; do not assume universal support.

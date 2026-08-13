# Motion Library Decisions

## Use CSS / WAAPI when
The effect is local, simple, and can remain declarative: hover/press feedback, basic reveals, clip-paths, transform/opacity transitions, small keyframe loops.

## Use CSS scroll-driven animations when
Progress can map directly to scroll/view progress and target browser support is acceptable. Provide fallback and reduced motion.

## Use Motion for React when
Animation state lives with React component state, layout/shared-element transitions matter, gesture support is needed, or concise spring-based UI interaction is desired.

## Use GSAP when
You need exact sequencing, labels, complex timelines, advanced scroll scrub/pin, FLIP, SVG/text choreography, or coordination across unrelated DOM/canvas systems.

## Use Lenis when
Smooth scrolling itself is part of the experience or DOM/WebGL synchronization benefits from a normalized scroll loop. Never add it automatically.

## Avoid
- two smooth-scroll libraries
- GSAP and Motion both animating the same property on the same element
- global animation loops when local triggers suffice
- `setState` on every scroll/pointer frame

## Use Barba.js when
A non-React multi-page site needs PJAX-like page lifecycle, per-route views, and leave/enter transition orchestration. Barba is not itself the animation library; pair it with one chosen animation engine and clean up page-specific code in lifecycle hooks/views.

## Use Rive when
An authored interactive vector asset has meaningful state-machine behavior. Account for runtime/WASM weight and isolate lifecycle.

## Use Lottie/dotLottie when
An authored vector timeline is enough. Prefer it over custom DOM animation when the motion already exists as a production asset and interactivity is simple.

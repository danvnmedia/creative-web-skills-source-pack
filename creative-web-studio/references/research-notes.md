# Research Notes and Source Trail

These notes distill patterns; do not copy proprietary prompts, assets, or code verbatim.

## MotionSites / MotionSite AI
Observed pattern: successful AI website prompts are concrete about page sections, visual composition, animation behavior, and target stack. The useful lesson is prompt specificity, not cloning a particular prompt. Public/cached material has described prompts optimized around React, Tailwind, Framer Motion/Motion, and media-heavy interactions.

## mfon-ukobo/cinematic-web-skill
Useful principles: story before effects, a central metaphor, scene-by-scene planning, purposeful entrances, motion grammar, progressive enhancement, anti-generic checks, and explicit WebGL/performance/accessibility QA. This pack restructures those ideas into narrower specialist workflows and adds prompt engineering, shader/WebGPU handling, rebuild ethics, device tiering, and static auditing.

## Motion official docs
Motion distinguishes scroll-triggered vs scroll-linked animation and supports layout/gesture animation with React primitives. Use it when UI state and animation are closely coupled.

## GSAP ScrollTrigger
Use for scrub, pin, snap, and timeline-centric scroll choreography where precise orchestration matters.

## Lenis
Designed for smooth scrolling while synchronizing DOM and WebGL; integrate with animation tickers carefully rather than creating competing loops.

## React Three Fiber / Three.js
Performance guidance emphasizes avoiding excessive mount/unmount churn, sharing geometry/materials, instancing repeated objects, mutating inside the render loop instead of React state, reducing draw calls, and disposing GPU resources.

## Spline / Rive / Theatre.js / Lottie
Treat authored runtimes as specialized tools: Spline for authored 3D, Rive for state-machine vector interaction, Theatre.js for timeline authoring, and Lottie for vector timeline playback.

## MDN / web.dev
Respect `prefers-reduced-motion`; native scroll-driven timelines and View Transitions are increasingly useful progressive enhancements. WebGPU remains limited-availability and needs fallback. Core Web Vitals default quality targets: LCP <= 2.5s, INP <= 200ms, CLS <= 0.1 at the 75th percentile.

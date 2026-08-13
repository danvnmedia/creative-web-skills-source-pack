# Shader Web Art — Showcase Map

| Source | What to study | Useful for |
|---|---|---|
| Codrops Creative Hub — https://tympanus.net/codrops/hub/ | WebGL image transitions, distortion, particles, GLSL, OGL, WebGPU, postprocessing | Technique exploration with visual demos |
| Infinite WebGL Gallery demo — https://codrops.com/Tutorials/InfiniteAutoScrollingGallery/ | DOM-like gallery behavior enhanced with WebGL | DOM↔canvas synchronization patterns |
| Three.js examples — https://threejs.org/examples/ | Materials, render targets, postprocessing, GPU techniques | Canonical implementation checks |
| R3F examples — https://r3f.docs.pmnd.rs/getting-started/examples | React integration of custom materials and render loops | React-based shader architecture |
| Awwwards WebGL inspiration — https://www.awwwards.com/websites/ | How GPU effects are integrated into complete brand experiences | Judge whether the effect supports the page, not just the demo |

## Reverse-engineer a shader reference

Describe it as a signal chain:

`input media/data -> coordinate transform -> distortion/mask/math -> compositing -> interaction driver -> fallback`

Example:

`image texture -> aspect-correct UV -> curl-noise offset -> mix original/distorted -> pointer velocity -> static crop fallback`

This produces transferable knowledge without copying shader source.

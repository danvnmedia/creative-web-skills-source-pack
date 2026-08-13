# 3D Runtime Decisions

## R3F/Drei
Best default for custom React 3D. Strong when you need direct scene control, glTF assets, cameras, controls, instancing, post-processing, or shaders.

## Spline
Best when the scene originates in Spline or visual authoring speed is more valuable than low-level control. Use the runtime/code API, lazy-load, and optimize the scene. Avoid many Spline embeds on one page.

## Theatre.js
Use for precise authored sequences and camera/object keyframes. Export production state; do not ship editor tooling unnecessarily.

## Rive/Lottie
Not substitutes for full 3D. Use them for vector/2D authored motion layers around the 3D experience.

## WebGPU
Modern GPU path with stronger capabilities, but browser support is not universal. Use capability detection and fallback. Do not make critical marketing content depend exclusively on it.

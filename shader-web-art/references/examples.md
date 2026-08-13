# Shader Web Art — Worked Examples

## Example 1 — Image hover displacement

**Input**

> Distort portfolio images on hover like a liquid lens.

**Approach**

- DOM image remains the semantic source.
- Mirror image into a DOM-aligned WebGL plane only when enhancement is active.
- Pointer velocity drives a low-amplitude displacement field.
- Damping returns the image to rest.

**Fallback**

Simple crop/scale hover; no effect on touch unless drag/scroll maps naturally.

---

## Example 2 — Noise dissolve chapter transition

**Input**

> Make one section erode into the next.

**Shader model**

Use a noise field + threshold controlled by `uProgress`. Add a narrow soft edge rather than stacking bloom/chromatic aberration by default.

**Narrative rule**

Use dissolve only if disappearance/material change belongs to the concept.

---

## Example 3 — Refractive product lens

**Input**

> The hero should have a glass lens that bends the background.

**Approach**

- Render background into a texture or use a controlled scene buffer.
- Distort UVs through a lens normal/SDF.
- Keep sample count modest.
- Avoid full-screen expensive multi-pass blur on mobile.

---

## Example 4 — Particle assembly

**Input**

> Thousands of particles should assemble into a logo/object on scroll.

**System**

- Store start/end positions in GPU-friendly buffers.
- Animate one normalized progress value.
- Use instancing/points or GPGPU when scale justifies it.
- Keep the semantic logo/text in DOM or provide an equivalent.

**Reduced motion**

Jump to the assembled state or use a short opacity reveal.

---

## Example 5 — Infinite DOM/WebGL gallery

**Input**

> Make a smooth image gallery where the images have shader distortion but captions remain crisp.

**Architecture**

- DOM owns layout, captions, links, accessibility.
- Canvas mirrors image bounds.
- One scheduler coordinates scroll, rect updates, and render.
- Recalculate layout on resize/content changes, not blindly every frame.

---

## Example 6 — Text as texture

**Input**

> Let a giant headline warp through a shader during one transition.

**Rule**

Keep real text available in DOM. Treat the shader copy as a visual duplicate. Avoid turning the entire site's typography into inaccessible texture-rendered glyphs.

---

## Example 7 — WebGPU compute experiment

**Input**

> Use WebGPU for a large interactive particle field.

**Progressive branch**

1. Detect `navigator.gpu`.
2. Request adapter/device and handle failure.
3. Run compute/storage-buffer path when available.
4. Fall back to WebGL particles or a poster when unavailable.
5. Keep interaction and content meaningful in every tier.

WebGPU is an enhancement, not a requirement unless the user explicitly controls the browser environment.

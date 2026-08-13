# Immersive 3D Web — Worked Examples

## Example 1 — Hero product turntable

**Input**

> Put a premium sneaker in 3D in the hero. It should respond to pointer movement but remain a usable commerce page.

**Architecture**

- Semantic hero copy and CTA remain DOM.
- Canvas is a visual layer, not the only content carrier.
- Preload one optimized GLB and environment map.
- Use pointer damping and tight rotation limits.
- Stop or lower rendering when the scene is idle/offscreen.

**Avoid**

Full physics, expensive depth-of-field, uncapped DPR, or a 30MB model for a gentle turntable.

---

## Example 2 — Scroll-scrubbed camera story

**Input**

> Scroll through a device and reveal internal components.

**Scene model**

- Camera path has 3–5 meaningful beats, not continuous random orbiting.
- Copy state changes at named progress ranges.
- Object transforms and camera movement are authored from the same normalized progress value.
- Avoid React state updates every frame.

**Tooling**

R3F + Drei + GSAP/ScrollTrigger or Theatre.js depending on authoring workflow.

---

## Example 3 — Exploded assembly

**Input**

> Show how a watch is assembled.

**Best pattern**

Store exploded/rest transforms per part. Scrub one `assemblyProgress` value between 0 and 1. Use labels to explain only the few components that matter to the story.

**Performance**

Reuse materials, compress textures, merge/instance where it does not break articulation, and avoid shadow-casting on every tiny part.

---

## Example 4 — World-as-navigation portfolio

**Input**

> I like the idea of Bruno Simon's portfolio, but I need an original concept for an architect.

**Transfer the principle, not the world**

- Principle: spatial exploration is the navigation model.
- New metaphor: a scale architectural site model with districts as projects.
- Change visual language, controls, geometry, content structure, and camera logic.
- Keep conventional project navigation available for accessibility and mobile.

---

## Example 5 — Spline-authored scene

**Input**

> Our designer already made the hero in Spline.

**Decision**

Use Spline runtime if the authored scene is production-appropriate. Do not immediately rebuild in Three.js.

**Audit before shipping**

- scene/model size
- runtime cost
- mobile behavior
- interaction mapping
- fallback poster
- whether the rest of the site needs a persistent WebGL context

---

## Example 6 — Device-tiered 3D

**Input**

> Desktop should be immersive but the site must work on mid-range phones.

**Tier plan**

- **High:** full model, reflections, selected post effects.
- **Medium:** lower DPR, simpler environment, reduced shadows/post.
- **Low/reduced motion:** static or lightly animated product poster, DOM content unchanged.

Do not make the mobile page a broken miniature of desktop choreography.

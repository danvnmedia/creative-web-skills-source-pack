# Motion Choreographer — Worked Examples

Use these examples to choose choreography, timing, and implementation boundaries.

## Example 1 — Pinned product explainer

**Input**

> As I scroll, keep the product visible and reveal four capabilities around it.

**Choreography**

- Pin only while the product needs persistent context.
- Map four copy states to one timeline.
- Use short overlaps so the outgoing label fades while the new detail moves into focus.
- Reverse scrolling must restore previous states exactly.

**Tool**

GSAP + ScrollTrigger. Keep product rendering independent if it lives in R3F.

**Mobile**

Replace long pinning with four short stacked steps or a swipe/step interaction.

---

## Example 2 — Shared-element case-study transition

**Input**

> Clicking a project thumbnail should feel like the card becomes the case-study hero.

**Choreography**

- Preserve the image crop and focal point during transition.
- Expand card bounds first; move metadata second.
- Do not fade the entire page to black unless the narrative requires a cut.

**Tool choice**

1. View Transitions API when routing/support fits.
2. Motion layout/shared layout for React UI.
3. GSAP FLIP for custom orchestration.

**Reduced motion**

Use a direct navigation with a short opacity transition.

---

## Example 3 — Kinetic typography hero

**Input**

> Make the hero headline feel energetic and editorial.

**Bad version**

Every character bounces independently for two seconds before the user can read it.

**Better version**

- Keep readable words visible within the first beat.
- Animate line masks and scale relationships, not random letters.
- Reuse one typographic transformation later as a chapter bridge.

**Timing family**

- intro cut: immediate
- line reveal: ~500–800ms
- supporting metadata: ~250–400ms

Tune to concept; do not mechanically apply values.

---

## Example 4 — Image gallery with pointer depth

**Input**

> I want portfolio images to react to the mouse and feel dimensional.

**Choreography**

- Map pointer offset to subtle translation/rotation.
- Apply damping; never chase the cursor 1:1.
- Keep text and click targets stable.
- Touch version uses drag or scroll progress, not nonexistent hover.

**Tool**

Motion spring values for DOM; GSAP quickTo for high-frequency pointer updates; WebGL only if image distortion is central.

---

## Example 5 — Rive stateful product illustration

**Input**

> The illustration should react to hover, press, and a selected mode.

**Tool**

Rive state machine rather than rebuilding complex authored vector motion in DOM.

**Integration rule**

Map app state to a small explicit Rive input contract. Pause offscreen where practical. Provide a static poster/reduced-motion state.

---

## Example 6 — Barba multi-page portfolio

**Input**

> This is a non-React multi-page site. I want seamless project transitions.

**Architecture**

- Barba handles navigation lifecycle/container swapping.
- GSAP handles the actual animation.
- Each page view owns setup and cleanup.
- Do not keep stale ScrollTriggers/listeners after navigation.

---

## Example 7 — Calm reduced-motion version

**Input**

> Preserve the premium feel for users who prefer reduced motion.

**Design response**

Do not simply disable every transition. Replace:

- large spatial travel → cuts/crossfades
- parallax → static layered composition
- long scrub → discrete step states
- continuous loops → poster frame
- scale-through-camera → crop change or color-field transition

The reduced-motion version should still look intentionally designed.

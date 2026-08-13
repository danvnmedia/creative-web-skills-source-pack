# Creative Site Rebuilder — Worked Examples

Use these examples to separate observable principles from protected expression.

## Example 1 — “I like Bruno Simon's portfolio”

**Observation**

The memorable principle is not “small car in a Three.js world.” It is that a navigable 3D world is simultaneously portfolio, personality, and interaction model.

**Reusable principles**

- world-as-navigation
- direct manipulation
- playful spatial discovery
- projects represented as places/objects

**Original rebuild for a landscape architect**

Use a topographic garden model with project zones, different camera/controls, different visual language, conventional DOM navigation, and mobile card fallback. Do not reproduce the car, course content, geometry, or level layout.

---

## Example 2 — Lusion-style spatial storytelling

**User request**

> Make our studio site feel like Lusion.

**Analysis response**

Translate “like Lusion” into measurable traits:

- high visual confidence
- 3D/interactive visuals tied to brand storytelling
- strong scene transitions
- sparse copy around visual moments

Then choose a different central metaphor, composition system, palette, typography, and signature interaction for the user's brand.

---

## Example 3 — MotionSites prompt reference

**User request**

> I like this MotionSites hero prompt. Make a version for my product.

**Allowed extraction**

Infer the prompt's structure: composition, sections, interaction states, media behavior, stack constraints, responsive intent.

**Do not**

Reproduce paid/proprietary prompt text verbatim. Write a new prompt from the user's product truth and the observed structural pattern.

---

## Example 4 — Codrops demo as technique reference

**User request**

> Use this WebGL gallery effect on my photographer portfolio.

**Rebuild path**

1. Identify the generic technique: DOM-synced image planes + shader deformation + infinite/continuous gallery logic.
2. Reimplement from public tutorial/demo principles or original code.
3. Change layout, pacing, shader character, typography, imagery, and navigation to fit the photographer.
4. Keep captions/links semantic in DOM.

---

## Example 5 — Screenshot-only reconstruction

**Input**

Three desktop screenshots, no live URL.

**Confidence labels**

- **Observed:** grid, type scale, crop, spacing, colors.
- **Probable:** sticky section inferred from repeated fixed visual position.
- **Unknown:** easing, exact animation duration, offscreen states.

Build the static hierarchy first. Propose two plausible motion interpretations instead of pretending unseen behavior is known.

---

## Example 6 — Existing code vs reference gap analysis

**Input**

A Next.js implementation and a reference URL.

**Output**

| Gap | Evidence | Priority | Fix |
|---|---|---:|---|
| Hero lacks focal contrast | image and headline compete at same scale | High | reduce image crop complexity; strengthen type hierarchy |
| Scroll reveal feels repetitive | all sections share the same fade-up | Medium | define 3 recurring motifs with scene-specific use |
| Mobile pin is too long | content remains fixed across multiple viewports | High | convert to stepped stack on small screens |

Prioritize perceptual/narrative gaps over pixel trivia.

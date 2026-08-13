# Creative Web Studio — Worked Examples

Use these examples to calibrate specificity and output quality. Reuse the reasoning pattern, not the surface design.

## Example 1 — AI hardware launch: precision assembly

**Input**

> Build a cinematic launch site for a pocket AI recorder. Premium, tactile, not generic SaaS. Next.js preferred.

**Experience thesis**

> The experience should feel like a precision instrument assembling itself because the product turns messy ambient conversation into structured memory.

**Art-direction choice**

- Macro product photography and technical annotation rather than neon gradients.
- Editorial black/ivory base with one restrained signal color.
- Motion motifs: magnetic alignment, focus pull, layer assembly.
- 3D reserved for one exploded-product scene.

**Scene plan**

1. **Identity:** oversized product silhouette emerges from darkness; copy is visible immediately.
2. **Capture:** waveform fragments converge into a clean transcript card.
3. **Inside the object:** pinned 3D exploded view with 3–4 labeled states.
4. **Memory:** calm editorial proof section with searchable conversation fragments.
5. **Resolution:** product reassembles into the purchase CTA.

**Stack**

Next.js + Tailwind + GSAP/ScrollTrigger for the narrative timeline; R3F/Drei only for the exploded scene; native CSS elsewhere.

**Acceptance criteria**

- The page still reads correctly with WebGL disabled.
- Mobile replaces the long 3D pin with short stepped states.
- Reduced motion uses cuts and opacity rather than camera travel.

---

## Example 2 — Healthcare SaaS: diagnostic clarity, not sci-fi

**Input**

> Design a modern site for a clinical workflow platform. I want motion, but it must feel trustworthy and easy to understand.

**Bad instinct**

Glass cards, glowing cyan blobs, medical cross icons, floating dashboards.

**Better direction**

Use the metaphor of **signal becoming legible**:

- Dense clinical inputs resolve into a clean care timeline.
- Sections arrive through cropping and alignment rather than spectacle.
- Product UI remains real DOM, sharp and readable.
- One interactive comparison demonstrates “before workflow / after workflow”.

**Motion grammar**

- reveal through alignment
- controlled blur-to-focus
- line continuity between steps
- short state transitions, no long scroll traps

**Stack**

Motion for React for UI/layout transitions; optional GSAP only if a multi-step pinned explainer truly needs it.

---

## Example 3 — Cultural archive: living collection

**Input**

> Create an immersive museum/archive site using photographs, oral histories, and maps.

**Experience thesis**

> The site should feel like opening drawers in a living archive because each object reveals a human story and a relationship to place.

**Signature interaction**

A persistent “artifact card” changes role across scenes: thumbnail → full-bleed image → map marker → metadata card. Preserve object continuity rather than starting a new effect in every section.

**Rendering strategy**

- DOM/SVG for text, metadata, and maps.
- CSS masks/GSAP FLIP for continuity.
- WebGL only if a spatial image field adds real discovery value.

---

## Example 4 — Fashion editorial: kinetic image choreography

**Input**

> Make an editorial fashion portfolio with strong motion, photography first, no 3D models.

**Direction**

- Treat each viewport as a magazine spread.
- Use hard cuts between restrained and high-energy scenes.
- Let image crops, text scale, and negative space carry identity.
- Use a shader only for one chapter transition if it reinforces material/texture.

**Stack**

CSS + GSAP + optional Curtains/OGL for image treatment. No Three.js scene graph unless the project actually needs spatial geometry.

---

## Example 5 — Developer tool: compiler-pipeline storytelling

**Input**

> Launch page for a code-analysis tool. The site should feel technical but not like every dark developer landing page.

**Central metaphor**

Source passes through a pipeline: raw code → parsed structure → finding → fix → confidence.

**Scene choreography**

Use one continuing line/node system across sections. The line becomes a code underline, graph edge, benchmark axis, then CTA frame. This creates continuity without expensive 3D.

**Stack**

SVG + Motion/GSAP. Prefer semantic code blocks and real text.

---

## Example 6 — Prompt-only delivery for a coding agent

**Input**

> Give me a prompt for Codex/Claude to build an Awwwards-style product site from this brief.

**Expected output structure**

1. Project intent and non-goals.
2. Experience thesis.
3. Visual system.
4. Scene-by-scene specification.
5. Motion tokens and interaction states.
6. Technology selection with explicit “do not use” rules.
7. Mobile + reduced-motion behavior.
8. Performance budget.
9. File/component architecture.
10. Acceptance checklist.

Do not output only adjectives such as “premium”, “futuristic”, or “cinematic”. Describe visible composition and behavior.

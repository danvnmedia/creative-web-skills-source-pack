# Showcase redesign after visual feedback - 2026-09-30

## Why this pass happened

The first implementation passed technical smoke checks but did not meet the expected visual quality. Screenshot review showed three concrete problems: Morrow's text obscured its photography, Kern's simple 3D blocks were used as the primary product image, and Asme's CSS landscapes looked schematic. The direction chosen for this pass was **bold experimental web**. Each showcase retains a distinct visual idea and a usable interaction.

## What changed

| Surface | Visual repair | Interaction / motion retained |
|---|---|---|
| Hub | Preview cards now use the actual local Morrow, Kern, and Asme assets; the remote Asme preview video and toy camera preview were removed | Four direct links remain keyboard reachable |
| Morrow Archive | Rebuilt as a dark fashion editorial with non-overlapping headline and image, three different cloth studies, responsive image crops, and shorter sections | Index dialog behavior, native scroll progress when supported, pointer depth, one-time reveals |
| Pelagic Signals | Shifted the field toward deep blue/cyan and reduced contour intensity; replaced the large salmon method block with a dark instrument chapter | WebGL sampling, adaptive resolution, impulse, reading controls and metric View Transition |
| Kern One | A local product photograph now carries the campaign hero; the interactive 3D specimen has its own labeled workspace; geometry and materials have more detail; the explode button describes its current action | Drag, scroll-linked disassembly, damped spring, reset, shutter and on-demand rendering |
| Asme | Local coast, highland, and desert photographs replace CSS polygon landscapes; the hero and approach now use the landscape imagery | Three field-note choices, stagger/reveal, card feedback, scroll-linked entry, day/night View Transition |

The Asme remote video was removed because it obscured the actual destination story and made the demo depend on an unrelated third-party file. Generated WebP assets total roughly 1.1 MB for all eight images, compared with about 18 MB of original PNG output.

## Asset provenance

All eight raster images were generated specifically for this repository with the built-in `imagegen` tool and converted with ImageMagick using `-strip -quality 82`. No photograph or code was copied from the reference repositories.

| Asset | Workspace path | Prompt used |
|---|---|---|
| Asme coast | `showcase-apps/asme-hero/public/assets/coast.webp` | Original cinematic editorial travel photograph, remote Atlantic coast at blue hour, charcoal cliffs, slate sea, pale beach, sea mist, tiny warm shelter light; photorealistic, dramatic but believable, left half quiet and dark for a cream headline, no text |
| Asme highland | `showcase-apps/asme-hero/public/assets/highland.webp` | Original premium travel-journal photograph, rugged highland valley, layered misty mountains, winding silver river, storm clouds with warm break in the horizon; tall portrait, dark lower fifth for title, no text |
| Asme desert | `showcase-apps/asme-hero/public/assets/desert.webp` | Original premium travel-journal photograph, copper-red escarpment and dunes after sunset, shadow bands and dust haze; tall portrait, dark lower fifth for title, no text |
| Kern camera | `showcase-sites/kern-one/assets/camera.webp` | Original high-end campaign photograph of a plausible fictional compact analog camera, matte-black body, bone-white top plate, teal lens reflection and vermilion shutter detail; dark studio, camera on right, left negative space, no logo or text |
| Morrow portrait | `showcase-sites/morrow-archive/assets/portrait.webp` | Original avant-garde fashion editorial portrait, model in sculptural oxblood pleated garment mid-turn against pale stone, directional light, tactile cloth, no text |
| Morrow silk | `showcase-sites/morrow-archive/assets/silk.webp` | Original experimental textile close-up, rust-red sheer silk in a sculptural wind-fold against charcoal, dramatic side light, left negative space, no text |
| Morrow dress | `showcase-sites/morrow-archive/assets/dress.webp` | Original conceptual fashion still life, pale pleated dress suspended in a sunlit concrete studio with long angular shadow, no person or text |
| Morrow afterimage | `showcase-sites/morrow-archive/assets/afterimage.webp` | Original fashion still life, suspended burgundy silk in a pale room casting a vivid red ghost-like shadow, realistic fabric, no person or text |

These prompt descriptions preserve the subject, composition, art direction, and negative constraints of the final generation set. The optimized files are the assets consumed by the site.

## Verification

Commands run from the repository root:

```powershell
npm.cmd run build
npm.cmd run lint
npm.cmd run test
npm.cmd run audit:static
npm.cmd run dev
npm.cmd run qa:browser -- .ai/evidence/browser/TASK-CREATIVE-002-final
```

The build, lint and repository tests passed. `python .ai/scripts/harness.py verify --profile native` also passed. The pre-existing audited Harness task remains in progress; this visual pass does not close its source-distribution regression gate. The static motion audit returned zero P1 findings and two P2 review notes for passive scroll listeners that schedule work with `requestAnimationFrame`. Playwright Chromium passed **15/15** cases: hub plus four showcases at 1440x900 desktop, 390x844 mobile, and 390x844 mobile with `prefers-reduced-motion: reduce`. The checks cover headings, horizontal overflow, local image loading, console/page errors, local HTTP failures, and the main interaction on each page. The screenshots and JSON report are local ignored artifacts in `.ai/evidence/browser/TASK-CREATIVE-002-final/`.

The first QA attempts surfaced a Kern scene visibility assumption and an assertion comparing transformed uppercase text. The test now scrolls the scene into view and checks the real button state/action. Kern's visible registered mark and the hub's arrows were also corrected from bad text encoding to HTML entities.

## Remaining limits

- This is local browser evidence. GitHub Pages has not been updated or inspected for this revision.
- A sustained 60 fps on physical low-power devices has not been measured. WebGL resolution adapts, the 3D scene renders on demand, and effects primarily use transforms/opacity, but a device trace is still needed for a performance claim.
- Kern's 3D geometry is a stylized technical specimen. The campaign photograph provides the realistic product view; replacing the specimen with a production-quality glTF model is the next visual investment if the camera demo is meant to represent a shippable commerce viewer.
- Pelagic numbers and Asme journeys are illustrative and are labeled as such in the UI.
- Google Fonts and the pinned Three.js module still require network access. Local photos and semantic/CSS fallbacks do not.
## Image generation prompt set

The following are the final prompts sent to the built-in imagegen tool. The resulting PNGs were inspected and converted to the WebP paths above.

1. **Asme coast:** Generate one original cinematic editorial travel photograph for a bold experimental web design showcase called Asme. A remote Atlantic coast at blue hour: immense charcoal cliffs, slate blue sea, a narrow pale beach and low sea mist, one tiny warm amber light from a distant shelter for human scale. Photorealistic natural location photography, sophisticated color grading, dramatic but believable light, rich fine detail and atmospheric depth, no people, no buildings in foreground, no typography, no logo, no borders, no collage. Landscape 16:9 composition: keep the LEFT 52% darker and quieter so a large cream serif headline can be overlaid legibly; strongest cliff and sea detail on the right. Premium independent travel journal art direction, film grain subtle. Asset for website hero, not a UI mockup.

2. **Kern camera:** Generate one original high-end product campaign photograph for a fictional experimental camera named KERN ONE. A plausible compact analog camera with a sculpted matte-black anodized aluminum body, understated bone-white top plate, deep multi-element circular lens with subtle teal reflections, one vivid vermilion shutter detail, tactile knurled metal dials, refined manufacturing details. Three-quarter front view on a dark graphite studio backdrop, hard directional side light creating crisp sculptural highlights and a long soft shadow. Bold experimental industrial-design campaign art direction, realistic premium product photography, not CGI toy blocks. No text, no logo, no watermark, no human hands, no UI. Wide landscape composition 16:9, camera occupies the RIGHT 60%, leave the LEFT 40% near-black negative space for white headline. Sharp and believable.

3. **Asme highland:** Generate an original premium travel-journal photograph for an experimental web showcase field note called Blue Hour, Inland. Vast rugged highland valley, dark mountain ridges layered in mist, a winding silver river reflecting the last light, low storm clouds and one warm break in the horizon. Photorealistic natural landscape photography with tactile film texture, restrained slate and moss palette, immersive depth, unexpectedly beautiful and believable. Tall portrait composition suitable for a full-bleed web card; keep the lower fifth dark and quiet for overlaid white title. No text, no UI, no people, no watermark.

4. **Asme desert:** Generate an original premium travel-journal photograph for an experimental web showcase field note called The Last Light. Expansive copper-red desert escarpment and sculpted dunes at the moment after sunset, strong bands of shadow, tiny dust haze glowing on the horizon, one subtle winding track for scale. Photorealistic natural landscape photography, editorial and cinematic but believable, rich terracotta/umber with soft rose sky, fine geology texture and depth. Tall portrait composition suitable for a full-bleed web card; keep the lower fifth dark and quiet for overlaid white title. No text, no UI, no people, no watermark.

5. **Morrow portrait:** Original avant-garde fashion editorial photograph for an experimental web archive called Morrow. Full-height portrait of a model in a dramatic sculptural oxblood-red pleated garment, caught mid-turn so the fabric forms a strong architectural silhouette, against a warm pale stone studio wall. Natural directional window light and long shadows, slight analog-film texture, quiet luxury with an unconventional editorial pose, tactile cloth detail. Portrait 4:5 composition with entire garment visible and breathing room around it. No typography, no logo, no watermark, no collage, no runway.

6. **Morrow silk:** Original experimental fashion editorial photograph for a web archive about fabric and memory. Extreme close-up of a rust-red sheer silk garment twisted into a flowing sculptural fold in the wind, visible fine weave and subtle translucent layers, dramatic side light against nearly black charcoal background. Abstract yet unmistakably real textile photography, premium art direction, fine film grain, warm highlights, no model face, no text, no collage, no logo, no watermark. Wide landscape composition 16:9, substantial dark negative space along left third for editorial title.

7. **Morrow dress:** Original conceptual fashion still-life photograph for an experimental web archive about cloth retaining movement. One pale ivory sculptural pleated dress suspended alone in a sunlit concrete studio, fabric lifting slightly as if a body just left it, long angular shadow on warm plaster, distant hint of oxidized red wall. Tactile realistic textile, art-gallery editorial photography, atmospheric and minimal but visually arresting. Wide landscape composition 16:9, no person, no typography, no logo, no watermark, no collage.

8. **Morrow afterimage:** Original avant-garde fashion still life photograph for the final chapter of an experimental web archive, theme: afterimage. A single suspended sculptural burgundy silk garment in a vast pale concrete room, late afternoon light passes through it and casts an unusually vivid red ghost-like shadow across the wall and floor. No person, no mannequin, believable tactile fabric, sophisticated fashion editorial, strong visual composition and material detail, warm muted palette, quiet but haunting. Wide landscape 16:9, no text, no logos, no watermark, no collage.

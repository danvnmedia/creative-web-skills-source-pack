# First-party Showcase Sites

These sites are original proof fixtures for the Creative Web Skills Pack. They intentionally use different composition systems, palettes, type strategies, and rendering tiers.

## Run

Serve this directory over HTTP because Kern One imports a pinned Three.js ES module:

```powershell
npx --yes serve . -l 4173
```

Then open `http://localhost:4173`.

## Demonstration matrix

| Site | Experience thesis | Base layer | Enhancement | Intentional fallback |
|---|---|---|---|---|
| Morrow Archive | Fabric behaves like memory held by light | Semantic editorial DOM + photography | Opening curtain, split-image echoes, pointer depth, and scroll-countermotion | Complete still layout; all reveals visible under reduced motion |
| Pelagic Signals | Ocean observations become a behavior rather than a chart | Semantic research narrative + CSS field | WebGL contour field, live depth probe, edge-aware readout, and click impulse | CSS contour field and full readable content |
| Kern One | A camera should reveal each photographic decision | Semantic product story + CSS product poster | Three.js self-assembly, drag/explode states, viewfinder HUD, and tactile shutter | Poster remains visible and status reports 3D failure |
| Asme | Curiosity should feel like entering a half-seen cinematic world | React form/navigation over a semantic full-screen composition | Video loop with cancellable RAF fades and liquid-glass surfaces | Black cinematic base, readable UI, and functional subscription form |

## Signature interactions

- **Morrow:** enter through the opening curtain, move across the hero image, then scroll to pull type and image in opposite directions.
- **Pelagic:** move or touch to sample depth/flow; click or tap to send a visible impulse through the contour field.
- **Kern:** watch the camera assemble, drag to inspect, toggle the exploded state, then fire the shutter control.
- **Asme:** watch the video fade in, submit the email form, and inspect the loop boundary where fade-out hands back to fade-in without CSS transitions.

## Manual acceptance checks

- The hub reaches every site with keyboard navigation.
- No page has accidental horizontal scrolling at 390px or 1440px widths.
- Reduced motion removes continuous or large movement without hiding content.
- Pelagic remains readable with WebGL disabled and pauses while hidden/offscreen.
- Kern remains product-specific before Three.js loads, supports pointer drag, and renders a nonblank canvas after load.
- Remote photography has meaningful alt text; canvas content is nonessential enhancement.
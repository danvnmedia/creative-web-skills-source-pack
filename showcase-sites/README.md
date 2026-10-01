# First-party Showcase Sites

These four original experiences demonstrate distinct creative-web roles. The hub at `/` links to each standalone page. The photographic assets in Asme, Kern, Morrow, and Pelagic were generated for this repository, converted to WebP, and committed with the source. Pelagic's WebGL refracts its local ocean artwork with a still-image fallback. Kern includes a first-party rendered 3D optical film with a local poster.

## Run

From the repository root:

```powershell
npm.cmd ci
npm.cmd ci --prefix showcase-apps/asme-hero
npm.cmd run build
npm.cmd run dev
```

Open `http://127.0.0.1:4173`. Kern imports a pinned Three.js ES module, so serve it over HTTP. The three static experiences also run from `showcase-sites/` under any static HTTP server. Asme's source app runs with `npm.cmd run dev --prefix showcase-apps/asme-hero`.

## Experiences

| Site | Visual direction | Useful interaction | Motion and fallback |
|---|---|---|---|
| Morrow Archive | Dark fashion editorial, tactile cloth photography, disciplined type | Open the keyboard-accessible index and move between three studies | Native scroll reading line where supported, scheduled pointer depth and one-time reveals; reduced motion displays all content immediately |
| Pelagic Signals | Luminous cobalt ocean vortex with an instrument-like reading panel | Sample the field and switch current, thermal, and salinity readings | Adaptive WebGL image refraction, impulse/probe feedback and metric View Transition; the still ocean artwork and readings survive WebGL failure |
| Kern One | Industrial camera campaign, cinematic optical film, then an interactive technical specimen | Play/pause the 3D film; drag the 3D object, explode/assemble it, reset, and trigger the shutter | Original 3D film pauses offscreen and under reduced motion; on-demand Three.js, damped spring assembly and view-timeline anatomy follow; local poster and product photograph remain fallbacks |
| Asme | Photographic travel atlas with three fictional destinations | Select field notes and switch the atmosphere | Staggered entry, card feedback, scroll-linked section motion, and day/night View Transition; all imagery is local and the content stays still under reduced motion |

Each page includes a short motion-technique note. The concept journeys and Pelagic readings are illustrative, not live travel inventory or measured ocean observations.

## Check

```powershell
npm.cmd run lint
npm.cmd run test
npm.cmd run audit:static
npm.cmd run qa:browser -- .ai/evidence/browser/my-fresh-run
```

The browser QA runs the hub and four experiences at 1440x900, 390x844, and 390x844 with reduced motion. It checks local images, overflow, browser errors, and the main control of each experience. Use a fresh output directory for each run. The full-page screenshots and JSON report are local evidence under ignored `.ai/evidence/browser/`.

The browser test is a functional baseline. Performance on a range of physical devices, exact sustained frame rate, and deployed GitHub Pages behavior require separate checks.

The Kern film is a four-second, 1280×720 H.264 loop rendered from `kern-one/film-stage.html` and `film-stage.js`. With the local preview server running, `node scripts/render-kern-film.mjs` recreates its frames and exports the MP4 and WebP poster. Generated frames stay under ignored `.ai/evidence/browser/`; the optimized film and poster are checked in so viewers do not need WebGL to watch it.

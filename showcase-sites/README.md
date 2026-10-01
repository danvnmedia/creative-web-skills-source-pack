# First-party Showcase Sites

These four original experiences demonstrate distinct creative-web roles. The hub at `/` links to each standalone page. The photographic assets in Asme, Kern, and Morrow were generated for this repository, converted to WebP, and committed with the source. Pelagic's field is procedural WebGL with a CSS fallback.

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
| Pelagic Signals | Deep-water instrument with animated procedural contours | Sample the field and switch current, thermal, and salinity readings | Adaptive WebGL resolution, impulse/probe feedback and metric View Transition; CSS field and readable values survive WebGL failure |
| Kern One | Industrial camera campaign followed by an interactive technical specimen | Drag the 3D object, explode/assemble it, reset, and trigger the shutter | On-demand Three.js, damped spring assembly and view-timeline anatomy; local product photograph remains the fallback |
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

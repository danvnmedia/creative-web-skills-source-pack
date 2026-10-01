> The original local QA is retained below. For the redesigned files and asset provenance, read [Showcase redesign after visual feedback](SHOWCASE-REDESIGN-2026-09-30.md).

# Browser QA for the four showcases — 2026-09-30

## Visual follow-up: ocean and 3D film

After the Pelagic and Kern visual changes, `npm.cmd run build`, `npm.cmd run lint`, `npm.cmd run test`, and `npm.cmd run audit:static` passed. The static auditor still reports only the two previously reviewed P2 scroll-listener notes. Chromium QA on the rebuilt local site passed **15/15** cases in `.ai/evidence/browser/TASK-CREATIVE-003-ocean-film-release/` (ignored local evidence). The Kern flow now waits for the local MP4, verifies playback and pause/resume at desktop and mobile sizes, and verifies that reduced motion leaves the video paused with its control disabled. Pelagic's thermal mode and reduced-motion still artwork remain covered. Desktop Chrome screenshots and mobile screenshot crops were inspected for composition and readability.

The test does not measure sustained frame rate on physical hardware. The film is a 24 fps pre-rendered H.264 asset; the interactive scene remains rendered on demand. Live Pages acceptance for this follow-up is reported separately after the PR is merged and `/revision.json` matches the new commit.

## Live release QA

PR [#7](https://github.com/danvnmedia/creative-web-skills-source-pack/pull/7) merged as `3b40c5da13f096a0549683a73ce7ae922774e837`. [GitHub Pages workflow](https://github.com/danvnmedia/creative-web-skills-source-pack/actions/runs/36804754384) succeeded, and the public `/revision.json` returned that exact SHA with HTTP 200.

In PowerShell, `$env:SHOWCASE_URL='https://danvnmedia.github.io/creative-web-skills-source-pack'; npm.cmd run qa:browser -- .ai/evidence/browser/TASK-CREATIVE-001-live-3b40c5d` ran Chromium against the deployed hub and all four demos at desktop, mobile, and mobile reduced motion sizes. **15/15 passed**. The report records zero page errors, console errors, local HTTP errors, and local request failures. It exercised the hub links and each demo's primary controls; 15 full-page PNGs and `browser-report.json` remain local under the ignored evidence directory.

The tests establish working live flows and responsive/reduced-motion behavior for this revision. They do not measure sustained frame rate on physical devices. Third-party fonts, video, and Three CDN availability can change.

## Earlier local QA

The root `npm.cmd run build` compiled Asme and generated `.pages-dist`. The local server `npm.cmd run dev` served that artifact at `http://127.0.0.1:4173`. `npm.cmd run qa:browser -- .ai/evidence/browser/TASK-CREATIVE-001-final2` launches Playwright Chromium and checks each of the four pages in three configurations: 1440 × 900 desktop, 390 × 844 mobile, and 390 × 844 mobile with `prefers-reduced-motion: reduce`.

The script asserts a nonempty heading, no horizontal overflow, no browser console/page errors, no failed local requests, and no local HTTP 4xx/5xx. It also exercises the primary control on every page: Morrow's Index/Escape, Pelagic's thermal mode, Kern's exploded view/shutter, and Asme's field-note/atmosphere selection. Reduced-motion checks verify the Morrow curtain is absent, Pelagic pauses its field, and Asme does not mount the decorative video. The Kern reduced-motion mode retains immediate controls and a static or 3D-ready status.

| Page | Desktop | Mobile | Mobile reduced | Motion technique |
|---|---|---|---|---|
| Morrow Archive | Pass | Pass | Pass | Native scroll progress when supported, scheduled pointer parallax, one-time reveals |
| Pelagic Signals | Pass | Pass | Pass | Adaptive WebGL shader, transform probe, metric View Transition |
| Kern One | Pass | Pass | Pass | On-demand Three.js, damped spring, view-timeline anatomy, shutter feedback |
| Asme | Pass | Pass | Pass | Staggered intro, card feedback, scroll entry, day/night View Transition |

**Result:** 12/12 browser cases passed in the final run. The JSON report and 12 full-page PNGs are local evidence in `.ai/evidence/browser/TASK-CREATIVE-001-final2/`. That directory is intentionally ignored by Git because screenshots, browser logs, and machine-specific paths are runtime artifacts. Selected images were visually inspected for hierarchy, overlap, clipping, and legibility; the earlier Kern overlap was corrected by moving the model lower and separating the headline from its body.

## Scope and remaining limits

- The real Chrome session also verified desktop/mobile navigation, Asme's selected field note and atmosphere, Morrow's keyboard menu, Pelagic's layer, and Kern's 3D loaded state. The Playwright run supplies reproducible screenshots and reduced-motion emulation.
- This section records the earlier local run; the live deployment check is documented above.
- Remote photos, fonts, the optional Asme video, and Kern's pinned Three.js CDN remain third-party dependencies. Semantic content and CSS/poster fallbacks continue to work if those enhancements fail; the exact availability of remote assets can change.
- The shader caps and adapts render resolution, the 3D scene renders on demand, and scroll/pointer work is scheduled on animation frames. A sustained 60 fps across devices is a target, not a measured guarantee; field devices and browser performance traces are the next performance gate.
- The static motion auditor reports no P1 issues after caching pointer geometry. Two P2 `scroll-listener` review notes remain for Morrow and Kern; both listeners are passive and schedule their work through `requestAnimationFrame`.
- Same-document View Transitions and CSS scroll timelines are progressive enhancements. The demos retain functional state and content in browsers without those APIs.

The first Playwright pass revealed two incorrect QA assertions for Kern's uppercased status and reduced-motion text. The test expectations were corrected to match visible product states; the later runs passed. In the restricted execution context, Chromium and Vite initially failed with `spawn EPERM`; both ran successfully in the permitted context. Playwright was installed as a root dev dependency, with its browser binary installed locally.

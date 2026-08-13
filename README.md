# Creative Web Skills Pack

[![License: MIT](https://img.shields.io/badge/License-MIT-f2c94c.svg)](LICENSE)
![Skills](https://img.shields.io/badge/skills-6-7c3aed.svg)
![Showcases](https://img.shields.io/badge/showcases-4-0f766e.svg)
[![Live showcase](https://img.shields.io/badge/live-showcase-d7ff3f.svg)](https://danvnmedia.github.io/creative-web-skills-source-pack/)

A focused collection of agent skills for art-directed websites: cinematic motion, interactive 3D, shaders, reference-led rebuilds, and production performance QA.

The pack is designed for ChatGPT and Codex workflows that need a coherent creative system—not a pile of disconnected visual effects. Every skill includes practical instructions, worked examples, curated references, accessibility constraints, mobile fallbacks, and evidence requirements.

> This is an independent community project. It is not an official OpenAI product and is not endorsed by OpenAI.

## What is included

| Skill | Use it for | Live page |
|---|---|---|
| [`creative-web-studio`](creative-web-studio/) | End-to-end art direction, scene planning, stack selection, prompts, architecture, budgets, and acceptance criteria. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/creative-web-studio/) |
| [`motion-choreographer`](motion-choreographer/) | GSAP, Motion, Lenis, native CSS/WAAPI, scroll choreography, page transitions, and interaction polish. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/motion-choreographer/) |
| [`immersive-3d-web`](immersive-3d-web/) | Three.js, React Three Fiber/Drei, glTF, Spline, Theatre.js, product viewers, and 3D performance. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/immersive-3d-web/) |
| [`shader-web-art`](shader-web-art/) | GLSL/WebGL, image effects, particles, displacement, refraction, DOM-to-canvas sync, and optional WebGPU. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/shader-web-art/) |
| [`creative-site-rebuilder`](creative-site-rebuilder/) | Analyze a URL, screenshot, recording, or existing frontend and rebuild its principles into an original implementation. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/creative-site-rebuilder/) |
| [`motion-performance-auditor`](motion-performance-auditor/) | Audit motion, WebGL, accessibility, responsiveness, Core Web Vitals risk, cleanup, and mobile behavior. | [Open ↗](https://danvnmedia.github.io/creative-web-skills-source-pack/motion-performance-auditor/) |

Use the narrowest skill that owns the task. Start with `creative-web-studio` when a request spans concept, implementation, motion, 3D, and QA.

## Install

Each top-level skill folder is standalone. A skill contains a required `SKILL.md`, optional references/scripts, and `agents/openai.yaml` metadata.

This layout follows the official [OpenAI guide for building and loading skills](https://learn.chatgpt.com/docs/build-skills).

### User-wide installation

Clone or download this repository, open a terminal in its root, and copy the six skill folders into your user skill directory.

PowerShell:

```powershell
$skillHome = Join-Path $HOME '.agents\skills'
New-Item -ItemType Directory -Force $skillHome | Out-Null

Copy-Item -Recurse -Force -Destination $skillHome -Path @(
  'creative-web-studio',
  'motion-choreographer',
  'immersive-3d-web',
  'shader-web-art',
  'creative-site-rebuilder',
  'motion-performance-auditor'
)
```

macOS/Linux:

```bash
mkdir -p "$HOME/.agents/skills"
cp -R \
  creative-web-studio \
  motion-choreographer \
  immersive-3d-web \
  shader-web-art \
  creative-site-rebuilder \
  motion-performance-auditor \
  "$HOME/.agents/skills/"
```

### Repository-scoped installation

To share the skills with everyone working in one repository, copy the desired skill folders into:

```text
<your-repository>/.agents/skills/
```

Codex detects skill changes automatically. Restart Codex if newly installed or updated skills do not appear.

## Use

Invoke a skill explicitly by mentioning it in the prompt:

```text
$creative-web-studio design a cinematic product launch with a strong mobile variant.
```

```text
$motion-choreographer refactor this hero animation and preserve reduced-motion behavior.
```

```text
$motion-performance-auditor audit this site before launch and provide runtime evidence.
```

Codex can also select a skill implicitly when a task matches the skill's `description`. In Codex CLI or the IDE extension, use `/skills` or type `$` to browse installed skills.

## Multi-skill operating model

For larger work, use this sequence:

1. `creative-web-studio` defines the experience thesis, scenes, rendering boundary, variants, budgets, and acceptance criteria.
2. One or more specialist skills implement only their owned layer and return changed assumptions plus proof.
3. `motion-performance-auditor` compares expected and observed behavior, then records residual risk.

The Studio handoff packet is the shared contract. It keeps art direction intact while motion, 3D, shaders, rebuild work, and QA happen in separate passes.

## First-party showcase

The repository includes four original field tests that exercise the pack's principles in runnable sites:

| Showcase | Demonstrates | Intentional fallback |
|---|---|---|
| [**Morrow Archive**](https://danvnmedia.github.io/creative-web-skills-source-pack/morrow-archive/) | Editorial composition, image choreography, keyboard navigation, restrained reveals | Complete still layout with all content visible under reduced motion |
| [**Pelagic Signals**](https://danvnmedia.github.io/creative-web-skills-source-pack/pelagic-signals/) | Semantic content over an interactive WebGL contour field | CSS field and fully readable content when WebGL is unavailable |
| [**Kern One**](https://danvnmedia.github.io/creative-web-skills-source-pack/kern-one/) | Three.js product assembly, drag, exploded view, adaptive DPR | Product-specific static poster and explicit 3D status |
| [**Asme**](https://danvnmedia.github.io/creative-web-skills-source-pack/asme-hero/) | React/TypeScript video hero, cancellable RAF fades, liquid-glass controls | Readable cinematic composition if video playback is unavailable |

See [`SHOWCASE-INDEX.md`](SHOWCASE-INDEX.md) for the complete reference index and [`showcase-sites/README.md`](showcase-sites/README.md) for the interaction checklist.

### Run locally

Requirements:

- Node.js 22 or newer for the React showcase build
- Python 3 only if you want to run the bundled static auditor

PowerShell:

```powershell
npm.cmd ci --prefix showcase-apps/asme-hero
npm.cmd run build --prefix showcase-apps/asme-hero
npx.cmd --yes serve showcase-sites -l 4173
```

macOS/Linux:

```bash
npm ci --prefix showcase-apps/asme-hero
npm run build --prefix showcase-apps/asme-hero
npx --yes serve showcase-sites -l 4173
```

Open `http://localhost:4173`.

### Publish with GitHub Pages

The included [Pages workflow](.github/workflows/pages.yml) rebuilds Asme, generates browsable pages for all six skills, and publishes the complete portal on every push to `main`.

After pushing the repository:

1. Open **Settings → Pages** in GitHub.
2. Select **GitHub Actions** as the publishing source.
3. Run **Deploy showcase to GitHub Pages**, or push to `main`.
4. Copy the live URL from the deployment summary.

See GitHub's guide to [using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for repository-level Pages settings.

## Static audit

The performance skill includes a dependency-free source scanner:

```bash
python motion-performance-auditor/scripts/creative_web_static_audit.py <project-path>
```

Use `--json` for machine-readable output:

```bash
python motion-performance-auditor/scripts/creative_web_static_audit.py <project-path> --json
```

The scanner discovers review candidates; it does not replace browser profiling, accessibility testing, or device evidence.

## Repository structure

```text
.
├── creative-web-studio/          # Creative direction and orchestration
├── motion-choreographer/         # DOM motion and interaction systems
├── immersive-3d-web/             # Three.js/R3F architecture and optimization
├── shader-web-art/                # GPU effects and shader workflows
├── creative-site-rebuilder/      # Reference analysis and original rebuilds
├── motion-performance-auditor/   # Performance/accessibility audit + scanner
├── showcase-apps/                # Showcase source applications
├── showcase-sites/               # Static showcase hub and field tests
└── .github/workflows/pages.yml   # GitHub Pages build/deploy workflow
```

## Principles

- Story before spectacle.
- Strong still frames before motion.
- Semantic DOM for content, navigation, SEO, and accessibility.
- The least complex renderer that can deliver the idea.
- Mobile and reduced motion as intentional variants.
- Measurable budgets and runtime evidence before calling work complete.
- References are studied for transferable principles, never cloned as protected expression.

## Contributing

Issues and pull requests are welcome. Keep contributions focused and reviewable:

1. Preserve the scope boundary of each skill.
2. Add or update examples when introducing a new pattern.
3. Include mobile, reduced-motion, accessibility, and fallback considerations.
4. Do not commit credentials, generated builds, dependency folders, or copyrighted third-party assets.
5. Build the showcase and run relevant checks before opening a pull request.

## Third-party services and media

The showcase loads some fonts, libraries, photography, and video from third-party CDNs. Those external resources remain subject to their respective owners' terms and are not relicensed by this repository. The MIT License applies to the source code and documentation committed here.

## License

Released under the [MIT License](LICENSE). You may use, copy, modify, merge, publish, distribute, sublicense, and sell copies, provided the license and copyright notice are retained.

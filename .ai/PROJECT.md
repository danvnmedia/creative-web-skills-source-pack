# Project Ground Truth

Fill this file with durable product facts. Keep it short enough to read every session.

## Product
- Name: Creative Web Skills Pack
- One-sentence purpose: Seven open-source agent skills and four runnable showcases for art-directed web experiences.
- Primary users: Designers and frontend developers using ChatGPT, Codex, or other coding agents.
- Core user job: Select a focused skill, build an original visual experience, and validate motion, accessibility, and performance.
- Current production status: GitHub Pages publishes from main; the deployed revision must be checked after each push.

## Success
- Primary value loop: Discover a skill -> follow its workflow -> run a relevant showcase -> verify the result.
- Product success signals: Correct skill routing, valid linked references, independently runnable demos, and reproducible browser checks.
- Reliability/SLO expectations: Base content and navigation remain usable when optional media, CDN, or WebGL fails.

## Architecture
- Frontend: Static showcase sites plus one React/TypeScript/Vite showcase under `showcase-apps/asme-hero`.
- Backend: None in the showcases.
- Data stores: None required.
- Auth/identity: None required.
- File/media storage: Locally generated photographic assets; Google Fonts and the pinned Three.js module use external CDNs.
- AI providers: None at runtime.
- Deployment: GitHub Actions builds the showcase portal for GitHub Pages.

## Sensitive boundaries
- Sensitive/regulated data: No credentials should be committed to this public repository.
- Tenant/account isolation: Not applicable to the static showcases.
- Destructive actions: Repository maintenance must preserve project-owned examples and source.
- External providers: GitHub Pages, Google Fonts, and the pinned Three.js CDN.

## Product constraints
- Cost constraints: Prefer native browser capabilities and existing dependencies; no new paid service.
- Accessibility/localization: Semantic content, keyboard focus, contrast, and reduced-motion variants.
- Device/browser priorities: Mobile and desktop Chromium browser checks, plus progressive fallback for limited features.
- Other non-negotiables: Original design/code; no copied third-party implementation without license review.

## AI routing intent
No AI provider is called by the showcases. Skill guidance may discuss providers in user projects, but this pack does not need runtime credentials.

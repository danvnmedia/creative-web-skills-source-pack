# Runtime Verification Standard

Static correctness is necessary but insufficient for a real web product.

## Six layers
1. **Static/build** — type/lint/unit/build.
2. **Boot** — the real server starts and health/readiness are meaningful.
3. **Browser smoke** — a real engine renders the app at mobile + desktop.
4. **Critical journey** — the changed user flow is actually exercised.
5. **Dependency reality** — remote media/APIs/fonts/proxies are reachable and fail gracefully.
6. **Production acceptance** — deployed revision works in its real environment.

## Browser evidence
A browser verification report should capture:
- URL/final URL;
- viewport;
- screenshot;
- `console.error`;
- uncaught page errors;
- failed requests;
- HTTP 4xx/5xx;
- user-flow assertion(s).
- a fresh output directory with an ownership manifest;
- mobile overflow/overlap assertions and visual screenshot review;
- durable before/after/reload evidence for saved state.

A page that visually renders while critical video/API requests return 403/404 is **not verified**.

## External assets
For critical external media/assets choose one of:
- bundle/host the asset under your control;
- use a stable authorized storage/CDN;
- implement an explicit fallback;
- accept the dependency risk as a documented product/reliability decision.

Avoid production experiences whose demo/content path depends only on random Wikimedia/Unsplash/CodePen/example URLs that were never probed from runtime.

## Suggested command

```bash
python .ai/scripts/record_evidence.py --task TASK-123 --check runtime-browser -- \
  node .ai/scripts/browser_smoke.mjs --url http://localhost:3000 --out .ai/evidence/browser/TASK-123 --fresh-output
```

For meaningful flows, project-native Playwright/Cypress tests should click/type/upload and assert the actual outcome. The generic smoke script is the floor, not the ceiling.

When a project has no e2e harness yet, create a declarative flow spec and run:

```bash
python .ai/scripts/record_evidence.py --task TASK-123 --check critical-flow -- \
  node .ai/scripts/browser_flow.mjs --spec .ai/evidence/flows/TASK-123.json --out .ai/evidence/browser/TASK-123-flow --fresh-output
```

The flow runner intentionally does not support arbitrary JavaScript/eval. It supports navigation/reload, click/fill/press, visibility/text/URL assertions, attribute capture/change/restoration, overflow/overlap assertions, screenshots, and console/network failure capture. This keeps proof reproducible instead of turning it into an agent-written browser monologue.

For asynchronous persistence, expose a stable observable attribute such as `data-saved-at` or a revision id. Capture it, perform the mutation, wait for the attribute to change, reload, and assert the durable value. Waiting for a transient "saving" label or a fixed timeout is insufficient.

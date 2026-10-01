# Migration: v5.3.0 to v5.4.1

v5.4.1 is built directly from canonical v5.3.0. Existing adaptive profiles, repo trust labels, verified checkpoints, 13-Skill routing matrix, ownership-aware install, Antigravity adapter, learning policy, loop guards, candidate closure, production acceptance, and runtime-state exclusions remain authoritative.

## New controls

- Run `python .ai/scripts/quarantine_scan.py --target <incoming-skill-or-plugin> --fail-on block` before installing or activating untrusted Skills/plugins/MCP configs.
- Use `skill_eval.py causal-report` for causal Skill claims. Loader/export changes must include `--require-exact-artifact` and a run whose `artifact_origin` is `reextracted-zip` or `published-package`.
- Set `traits.borrowed_browser_session=true` only when a task borrows an existing logged-in browser context. Record `browser-lease` evidence; disposable Playwright/headless contexts do not require it.
- Release with `package_release.py`; the final ZIP must pass source verification, exact ZIP verification, re-extracted verification, SBOM checks, and witness verification.

No existing project should be forced from native to portable/audited merely because these controls exist. Profiles still govern persistence ceremony only.

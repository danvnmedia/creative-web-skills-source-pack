# Verify Runtime
1. Read `.ai/COMMANDS.json`, `.ai/REPO_MAP.json`, and the active task.
2. Use only confirmed/observed runtime commands; verify inferred hints before relying on them.
3. Start the actual app with a real command.
4. Exercise the changed critical user flow in a browser.
5. Capture screenshots, console/page errors, request failures, HTTP errors.
6. Scan/probe critical external dependencies.
7. Fix observed failures and rerun.
8. Record the final browser/e2e command as `runtime-browser` and `critical-flow` evidence as applicable.
9. For portable/audited tasks, checkpoint only after fresh evidence proves a meaningful boundary, then record `verified-progress`.
10. Run `evidence_gate.py`.

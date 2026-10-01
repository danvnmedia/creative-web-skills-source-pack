# Start Task
1. Read `AGENTS.md` + project/state/resume/commands/quality.
2. Run/inspect `.ai/REPO_MAP.json`; do not execute inferred commands.
3. Inspect the real code/runtime relevant to the request.
4. Classify PATCH/FEATURE/PRODUCT/CRITICAL.
5. Create/update `.ai/tasks/<TASK-ID>.json` and `.ai/STATE.json` active_task.
6. Set task traits so automatic verification gates apply.
7. Resolve `native|portable|audited` with `.ai/scripts/execution_profile.py --write`.
8. Load only relevant Skills.
9. Implement unless a Human Gate is required.

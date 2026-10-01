# Trusted Repository Mapping

v5.3 maps an existing repository before assuming commands, runtime defaults, or agent surfaces.

```bash
python .ai/scripts/repo_mapping.py --root . --out .ai/REPO_MAP.json
python .ai/scripts/bootstrap_project.py --write
```

Every mapped fact has a trust label:

- `observed` — directly read from a repository file/path;
- `declared` — explicitly stated by the human/project but not independently observed yet;
- `inferred` — heuristic/convention only.

**Inferred is never executable truth.** For example, a Next.js dependency may justify an inferred `http://localhost:3000` hint, but the harness must still start the real app and observe the actual URL before runtime verification.

`bootstrap_project.py --write` auto-enables only commands that exist as observed repository scripts. Python `pytest` and framework-default URLs remain hints until confirmed.

Use the repo map to detect existing CI, testing, agent, and runtime surfaces before adding overlapping harness mechanisms. Prefer integration with a working project-native mechanism over creating a competing second source of truth.

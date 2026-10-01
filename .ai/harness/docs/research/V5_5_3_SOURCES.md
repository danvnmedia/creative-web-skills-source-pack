# v5.5.3 public-source research record

Research window: 2026-09-19. Mechanisms were independently reimplemented; no third-party implementation was vendored.

## Adopted

- `NVIDIA/SkillSpector` (Apache-2.0; active through 2026-09-18): incomplete-analysis truth and fail-closed resource-bound handling. Adopted as a local completeness contract, not as a dependency.
- `alibaba/skill-up` (Apache-2.0; active through 2026-09-18; v0.12.0 preparation visible): deterministic E2E runs are separated from full/model-dependent E2E. Adopted as auto-discovered deterministic release regression coverage plus local runner provenance.
- `LeoInTheLoop/skillEval` (MIT; created 2026-07-29): target Skill and visible catalog are separate evaluation dimensions. Adopted as a full-catalog/target-excluded matrix contract. Live causal claims still require trusted telemetry.
- `CosmosMind-ai/RSI-Harness` (created 2026-09-03; repository metadata did not declare a license at review time): upstream surface extraction can expose newly added host keys. Only the public mechanism was reimplemented; no source was copied.

## Reviewed but not promoted

- `tardigrde/agent-skill-eval`: isolated workspaces and deterministic assertions are useful but overlap v5.5.2 isolation/transaction controls.
- `highflame-ai/ramparts`, `snyk/agent-scan`, `Teycir/SkillsGuard`: useful security ideas, but current incremental gaps are covered by the v5.5.3 completeness control without adding a scanner dependency or executing untrusted MCP servers.
- worktree/multi-agent orchestration projects: not promoted because this remains a single-primary-agent Harness and no measured benefit justified added orchestration complexity.

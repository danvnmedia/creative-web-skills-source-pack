# Codex Product Harness v5.5.10

Canonical compatibility/quality baseline: 5.3.0. Exact implementation parent: 5.5.9.
See `docs/HARNESS_FEEDBACK_V5_5_7.md` for the 16-item field triage, and
`docs/MIGRATION_V5_5_6_TO_V5_5_7.md` for install/CI/Windows/release instructions.
This release preserves raw artifact/ownership hashes and all 13 canonical Skills.
Windows simulation and Linux tests are not native Windows or live Skill acceptance.

## Retained capabilities from earlier releases

## New in v5.5.6: task-bound prompting, without a 14th Skill

An on-demand [brief-task workflow](.agents/workflows/brief-task.md) helps the existing
agent clarify an outcome, preserve intent and render a compact brief from the actual
task. `prompt_brief.py` compiles, lints, repairs and prepares verified-context handoffs;
it does not understand arbitrary prose without the agent, execute product changes,
choose a model, grant permissions or certify Skill activation. No LLM dependency.

Human intent -> existing agent -> canonical task -> deterministic brief -> existing
Skills and trait-derived gates -> real execution evidence. Prompt-authoring requests
only produce a prompt; implementation requests must not stop at producing prompts.
The receiving agent's execute/plan-only mode is a separate choice.

Start with [Vietnamese usage](docs/HUONG_DAN_PROMPT_V5_5_6_VI.md),
[contract and limitations](docs/PROMPT_BRIEF_V5_5_6.md), and
[migration](docs/MIGRATION_V5_5_5_TO_V5_5_6.md).
All 13 canonical Skills and v5.5.5 execution-boundary fixes are preserved.



Canonical baseline: 5.3.0. Parent: 5.5.4. See
`docs/WINDOWS_EXECUTION_V5_5_5.md` and `docs/MIGRATION_V5_5_4_TO_V5_5_5.md`.
Native Windows acceptance is separate from Linux/WSL or newline fixture success.

## Inherited 5.5.4 foundation

Security-coverage hardening: canonical baseline **5.3.0**, implementation parent **5.5.3**. See
`docs/SECURITY_COVERAGE_V5_5_4.md` and `docs/MIGRATION_V5_5_3_TO_V5_5_4.md`. All v5.5.3 completeness/drift controls remain preserved.
The 13 canonical Skills are unchanged. Static scan hardening is not a claim of live-host or sandbox immunity.


The inherited v5.5.1 foundation completes the v5.5 evidence architecture and operator reliability work while preserving the canonical v5.3.0 contract and all 13 canonical Skills byte-for-byte. It adds canonical task identity, atomic evidence events, split source/task/lifecycle digests, boundary-aware verification, Windows-safe temp/ACL handling, and an explicit Harness command plane.

## v5.5.4 security coverage hardening

- Opaque executable/compiled payloads (`.pyc`, native libraries/binaries, JVM/WASM/Node artifacts, plus common executable magic) make deterministic static Skill analysis explicitly **partial** and release-blocking instead of silently appearing clean.
- Python-source scanning adds bounded AST sink resolution for direct and statically reconstructable reflective `exec`/`eval`, plus review-level runtime loader/subprocess sinks; this is additive to existing regex rules and never executes target code.
- Python syntax that cannot be parsed produces an explicit incomplete-analysis signal rather than an absence-of-findings claim.
- No canonical Skill text changed; v5.5.3 deterministic E2E, catalog-routing, host-surface and analysis-completeness controls remain intact.

## v5.5.3 completeness and drift hardening

- Security scans distinguish complete analysis from partial/failed analysis; a baseline cannot convert resource-limit truncation into a clean result.
- Release regression coverage auto-discovers every deterministic `*_regression_test.py`; live/external E2E remains separate.
- A 39-case full-catalog Skill routing contract checks target-vs-visible-catalog behavior without treating matrix fixtures as activation proof.
- Pinned host-surface snapshots can fail on newly observed, unclassified upstream capabilities without claiming host parity.


## v5.4.4 Skill supply-chain + compaction truth hardening

- **Skill Security Gate**: deterministic, fail-closed pre-install/import/promotion scanning with exact bundle hashes, resource ceilings, compression-ratio checks, exact finding baselines, and truthful static-only labels.
- **Compaction Truth Barrier**: evidence-lineage checkpoints with stable event IDs, producer exit status, closed tool-call/result state, explicit verified claims, and mandatory post-compaction reverification.
- **No Skill drift**: all 13 canonical `SKILL.md` files remain byte-identical to v5.3.0.

- Collision-safe installation: generic project roots are never blindly owned or overwritten; Harness release metadata/docs live under `.ai/harness/**` after install.
- Plan-first transactions: the first installer run is read-only; apply requires the exact `plan_digest`, compare-and-swap checks every planned container, and rollback restores changed targets on failure.
- Managed pointer blocks: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `ANTIGRAVITY.md`, and the three immutable-Skill companion doc paths preserve all project content outside Harness markers.
- Source vs installed boundary: release-package validation remains strict, while installed self-test checks only Harness-owned state and never mistakes application `.git`, `node_modules`, config, or build output for Harness residue.
- Harness metadata resolution: installed tools read `.ai/harness/VERSION`, never the application's root `VERSION`.
- v5.4.2 waiver/controller/MCP controls and v5.4.1 causal-eval/quarantine/browser/provenance controls remain intact.

**Evidence-driven product engineering that is adaptive, measurable, trust-aware, and portable.**

v5.5.4 was an additive upgrade on the canonical v5.3.0 contract. It preserves every v5.3 execution, trust, checkpoint, Skill-acceptance, ownership, Antigravity, security, closure, runtime, and exact-artifact invariant; retains all v5.5.3 controls; and closes two static-analysis truth gaps: opaque executable payloads and statically reconstructable reflective Python execution.

## v5.5.1 completion hardening

v5.5.1 adds a declarative `.ai/CHECK_CATALOG.json` and `verify_all.py` so shared regressions execute once while evidence can satisfy every catalog-declared check; a separate runtime-candidate digest so deployment metadata does not stale source-only checks; host-receipt browser capability receipts with project-local/transient distinctions; and `HARNESS_TEMP_DIR` plus writable-probe temp fallback for managed Windows sandboxes.

## What v5.4.1-v5.5.1 add on top of canonical v5.3.0

1. **Cost-bounded causal Skill acceptance** — paired with/without-Skill runs must keep runtime identity aligned, avoid quality regression, show measurable lift, and stay inside explicit token/duration/cost budgets. Loader/export changes require an exact exported artifact run.
2. **Static Skill/MCP quarantine** — deterministic pre-install/pre-activation scanning rejects traversal, escaping symlinks, secret material and high-confidence dangerous patterns without executing MCP commands.
3. **Borrowed-browser lease** — disposable headless contexts remain frictionless; borrowing a real logged-in tab/window requires a narrow, expiring, return-verified lease.
4. **Release provenance** — releases include SPDX-2.3 SBOM, exact-artifact witness, optional Ed25519 signature, exact ZIP re-extraction verification, and truthful distinction between a mathematically valid embedded signature and an out-of-band trusted signer identity.
5. **Exact portable-plugin acceptance** — Agent Plugins skills-only export carries a file-hash lock and is re-extracted/reverified before success. Host policy parity is still never claimed.
6. **Collision-safe transactional install** — generic root metadata/docs are project-protected, Harness metadata is namespaced, root integration uses owned marker blocks, and apply requires a fresh plan digest with CAS + rollback.
7. **Source/installed validation split** — source artifact verification stays strict; installed self-test validates the Harness-owned subset only and explicitly refuses source-release operations inside an app repo.
8. **Harness metadata namespace** — installed runtime tools resolve Harness version from `.ai/harness/VERSION`, preventing an application's `VERSION` from contaminating exports or reports.

### Preserved v5.3 invariants

1. **Adaptive execution depth** — `native`, `portable`, and `audited` profiles choose the lightest persistence ceremony that still preserves safe completion. Product quality gates never disappear just because the task stays native.
2. **Verified-progress checkpoints** — only milestones backed by fresh passing evidence may survive a session/model/context boundary. Failed/rejected work stays evidence, not progress.
3. **Trusted repo mapping** — deterministic `observed / declared / inferred` labels prevent framework conventions or guessed commands from silently becoming executable truth.
4. **Skill runtime acceptance contract** — package presence is separated from actual activation and causal value. Positive/negative routing cases ship for all 13 Skills; self-report is explicitly not activation evidence.
5. **Skill-change quality gate** — `traits.skill_modification=true` requires `skill-eval-live`; deeper paired with/without-Skill evaluation is supported without forcing an external dependency on every project.
6. **Optional Agent Plugins v1 export** — export the canonical 13-Skill surface as a portable skills-only plugin while keeping install, sandbox, permissions, evidence, and release policy host-specific.
7. **Existing-repo integration before duplication** — repo mapping inventories project-native CI, test, runtime, and agent surfaces before the harness adds or assumes competing mechanisms.
8. **Everything from v5.2.1** — ownership-aware installation/repair, Antigravity first-class adapter, cross-harness source ownership, provenance-safe learning, harness security, retry loop guards, candidate closure, production acceptance, browser/runtime evidence, and exact-artifact verification.

## Install / upgrade

Extract the trusted release **outside** the target project. The first run is read-only and prints a `plan_digest`:

```bash
python INSTALL_HARNESS.py --target /path/to/project
```

Review the plan, then apply exactly that observed state:

```bash
python INSTALL_HARNESS.py --target /path/to/project --apply --confirm <plan_digest>
cd /path/to/project
python .ai/scripts/bootstrap_project.py --write
python .ai/scripts/harness_doctor.py
python .ai/scripts/self_test.py --context installed
python .ai/scripts/skill_eval.py validate
```

Do **not** copy the release tree wholesale into the project root. `README.md`, `VERSION`, `CHANGELOG.md`, `LICENSE*`, `docs/**`, `templates/**`, and release packaging files are project-protected. Harness metadata/docs are relocated beneath `.ai/harness/**`; agent entrypoints are integrated through marker-scoped blocks only.

`bootstrap_project.py --write` auto-enables only **observed repository scripts**. Inferred runtime URLs or generic commands remain labeled hints in `.ai/REPO_MAP.json` until confirmed.

## Start a task

Create/update `.ai/tasks/<TASK-ID>.json` from schema-v5 `.ai/TASK_TEMPLATE.json`, then resolve the execution profile:

```bash
python .ai/scripts/execution_profile.py --task TASK-123 --write
```

- `native` — finish and verify in the current session; no extra checkpoint ceremony.
- `portable` — expected session/model/context boundary or external wait; verified checkpoint required.
- `audited` — critical/security/release/harness work; verified checkpoint plus the full trait-derived evidence.

The profile controls persistence overhead, **not** product quality. A native web task still requires browser + critical-flow evidence when its traits require them.

## Portable / audited checkpoint

After a meaningful verified boundary:

```bash
python .ai/scripts/verified_checkpoint.py checkpoint \
  --task TASK-123 \
  --completed "Durable save survives reload" \
  --next-action "Verify degraded provider fallback" \
  --check state-recovery

python .ai/scripts/record_evidence.py \
  --task TASK-123 --check verified-progress -- \
  python .ai/scripts/verified_checkpoint.py validate --task TASK-123
```

Resume from observable facts only:

```bash
python .ai/scripts/verified_checkpoint.py resume --task TASK-123
```

## Skill runtime acceptance

Validate the shipped routing matrix and prepare answer-key-safe prompts:

```bash
python .ai/scripts/skill_eval.py validate
python .ai/scripts/skill_eval.py prepare \
  --out .ai/evidence/skill-eval-tasks.jsonl \
  --runs-per-case 2
```

A runtime adapter may record trustworthy activation observations to JSONL, then:

```bash
python .ai/scripts/skill_eval.py report \
  --runs .ai/evidence/skill-eval-runs.jsonl \
  --out .ai/evidence/skill-eval-report.json \
  --fail-on-regression
```

**Do not use the agent saying “I used ui-ux-design” as activation evidence.** Native/trace attribution is accepted; self-report/inference/unavailable telemetry is not. When the host cannot expose trustworthy activation attribution, use a paired causal with/without-Skill evaluation for quality claims or record an explicit time-bounded waiver.

## Optional portable Skill export

```bash
python .ai/scripts/export_agent_plugin.py \
  --out /tmp/codex-product-harness-skills.zip
```

The export follows the public Agent Plugins v1 layout (`plugin.json` + `skills/`) but intentionally excludes host-specific installation, permission, sandbox, hook, evidence, and release semantics.

## Normal candidate / production path

```bash
python .ai/scripts/workspace_hygiene.py --strict --allow-evidence
python .ai/scripts/evidence_gate.py --task TASK-123
python .ai/scripts/close_task.py --task TASK-123
python .ai/scripts/evidence_gate.py --task TASK-123
python .ai/scripts/completion_report.py --task TASK-123 --out .ai/evidence/completion-TASK-123.md
```

Production release still requires the exact deployed revision plus `production-smoke` and `production-critical-flow` before `accept_release.py` can mark it accepted.

## Important v5.4.x files

- `.ai/INSTALL_POLICY.json` — collision-safe namespace, managed-block, plan/digest/CAS/rollback contract.
- `.ai/SOURCE_DISTRIBUTION.json` — source-release marker; deliberately absent after installation.
- `.ai/scripts/install_plan.py` — read-only install planner and transactional apply engine.
- `.ai/scripts/verify_installation.py` — installed-runtime verifier that ignores unrelated product residue by design.
- `.ai/EXECUTION_POLICY.json` — native/portable/audited selection and profile gates.
- `.ai/SKILL_EVAL_POLICY.json` — activation attribution plus causal quality/efficiency budgets.
- `.ai/QUARANTINE_POLICY.json` — static pre-install/pre-activation safety gate.
- `.ai/BROWSER_LEASE_POLICY.json` — containment contract for borrowed logged-in browser contexts.
- `.ai/RELEASE_POLICY.json` — SBOM/witness/exact-artifact provenance rules.
- `.ai/evals/skill-routing.json` — positive/negative routing cases for all 13 Skills.
- `.ai/scripts/execution_profile.py` — deterministic profile resolver.
- `.ai/scripts/repo_mapping.py` — non-executing repo map with trust labels.
- `.ai/scripts/verified_checkpoint.py` — evidence-backed durable progress.
- `.ai/scripts/skill_eval.py` — routing eval contract, answer-key-safe preparation, and trusted telemetry grading.
- `.ai/scripts/export_agent_plugin.py` — optional skills-only Agent Plugins v1 export.
- `docs/harness/ADAPTIVE_EXECUTION.md` — profile semantics.
- `docs/harness/SKILL_RUNTIME_ACCEPTANCE.md` — package vs activation vs causal value.
- `docs/harness/TRUSTED_REPO_MAPPING.md` — observed/declared/inferred rules.
- `docs/harness/VERIFIED_PROGRESS.md` — long-horizon checkpoint rules.
- `docs/harness/AGENT_PLUGIN_EXPORT.md` — portable export boundary.
- `docs/research/V5_3_SOURCES.md` — public source/provenance notes.
- `docs/MIGRATION_V5_2_1_TO_V5_3.md` — inherited baseline migration guide.
- `docs/MIGRATION_V5_3_TO_V5_4_1.md` — canonical v5.3.0 → v5.4.1 migration guide.
- `docs/MIGRATION_V5_4_1_TO_V5_4_2.md` — waiver/controller/MCP hardening migration guide.
- `docs/MIGRATION_V5_4_2_TO_V5_4_3.md` — collision-safe install and source/installed-boundary migration guide.
- `docs/harness/SOURCE_VS_INSTALLED_BOUNDARY.md` — why package verification and installed self-test are intentionally separate.

## Philosophy

**Human steers. Codex builds. Runtime tells the truth. Sensors verify. Persist only verified progress. Inference stays labeled. Skills must earn their context.**

- `docs/MIGRATION_V5_4_3_TO_V5_4_4.md` — Skill security and compaction-truth migration guide.
- `docs/harness/SKILL_SECURITY_GATE.md` — deterministic pre-install Skill security contract.
- `docs/harness/COMPACTION_TRUTH_BARRIER.md` — verified-progress lineage across compaction/context boundaries.

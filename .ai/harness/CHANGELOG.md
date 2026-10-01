# Changelog

## 5.5.10 - Actual-target Budget Gate for AI Fallbacks (2026-09-27)

- Harden provider policy to evaluate the **actual billing target** before every paid fallback; a zero-cost primary never exempts a paid fallback from budget enforcement.
- Require read-only budget verdicts before an atomic reservation, reserve only the selected target, and release reservations for targets that never execute. Unknown paid-target cost/budget scope fails closed.
- Add fallback-graph preflight requirements so malformed targets or paid fallbacks missing capability/budget metadata are rejected before runtime.
- Add an optional pure reference evaluator (`provider_route_budget.py`) plus deterministic v5.5.10 regressions covering free-primary/paid-fallback budget bypass, unknown target metadata, reservation semantics, and v2 compatibility. No live or paid provider call is made.
- Keep all 13 canonical Skill files byte-identical to v5.3.0 and preserve v5.5.9 release-doctor/marker/summary behavior.

## 5.5.9 - Release Preflight + Authorized Capacity Routing (2026-09-26)

- Add read-only `release_doctor.py` to separate candidate/closure/HEAD/upstream/marker/deploy hints and print one safe next action without pushing or deploying.
- Warn at task validation time when a production-release task lacks a revision marker, before expensive production acceptance steps.
- Add optional `record_evidence.py --summary` one-line output while preserving the legacy JSON default and stored evidence bytes.
- Clarify provider policy v2: legitimate free/free and budget-authorized free/paid failover across independent eligible quota scopes is allowed; same-scope keys are not new capacity; provider restrictions and unapproved spend caps remain fail-closed. Canonical 13 Skill files are byte-preserved.
- Add deterministic v5.5.9 regressions for release-doctor truth labels, marker readiness, compact output compatibility, and provider-policy v1/v2 compatibility.

## 5.5.8 - Recorder Success / Failure Precedence (2026-09-22)

- Reproduce a zero-exit DNS-labelled successful check recorded as BLOCKED in both
  exact v5.5.6 and v5.5.7, including the consequent evidence-gate rejection.
- Keep timeout first, then accept zero effective exit before failure-output
  heuristics. Nonzero environment/security/dependency/product classification,
  workspace mutation rejection and Skill live-evidence validation remain active.
- Add deterministic unit/subprocess/gate regressions and a catalog runner;
  auto-discovered release regression includes the new script. Do not rewrite old
  events, closure receipts or application tasks such as INITIAL-LOAD-BUDGET.
- Keep v5.3 baseline, 13 raw canonical Skills, existing policies/gates and v5.5.7
  fixes. Archive the exact parent lineage; do not weaken source/installed tests.
- This is process/evidence correctness, not native Windows/live Skill/product or
  production UX acceptance. See docs/RECORDER_STATUS_V5_5_8.md.

## 5.5.7 - Field Feedback: Install and Release Boundaries

- Plan-bound command reference audit and CI ownership-state warnings; no automatic CI rewrite.
- Exact-path managed Git attributes, raw hash verification, explicit prior-hash CRLF repair.
- Closure receipt creation no longer changes runtime candidate identity; real URL/revision/artifact remain bound.
- Actionable immutable-closure, terminal-task, missing-manifest and observed-revision guidance.
- Occupied-port refusal, optional bounded local JSON identity, conservative Windows batch argv resolution.
- Mode enum in schema, advisory trait/Skill and unknown-check diagnostics, two full task examples.
- Optional project-owned UX token schema/validator (structure only, not design or accessibility acceptance).
- 13 canonical SKILL.md files unchanged. No new paid APIs or upstream code imported.

## 5.5.6 - Task-bound Prompt Briefs (2026-09-21)

Parent 5.5.5; canonical compatibility/quality baseline 5.3.0.

- Add on-demand brief-task workflow, not a new autonomous Skill/catalog entry.
- Compile canonical tasks for Codex, Claude, Gemini and Antigravity in Vietnamese/English.
- Separate prompt authoring from recipient execution; preserve all trait/profile gates.
- Add optional prompt_context with digest-bound decisions, non-goals, refs and unknowns.
- Reuse canonical verified checkpoints; keep non-pass history distinct from progress.
- Add immutable bounded runtime capsules; compare to canonical state on use, not just hash.
- Add 59 deterministic regressions and a prompt-brief-contract Harness-change check.
- Keep existing task digests unchanged when optional prompt_context is absent.
- No model/API control table, hidden reasoning, paid call, global install or permission grant.

## 5.5.5 - Windows Execution Boundary Hardening (2026-09-21)

- Close the bounded capture reader pipe on completion; retain and regress the prior ResourceWarning.

- Fix installed full-suite routing/version before work starts.
- Prevent temp-inside-source copy recursion; add explicit bounded scratch routing.
- Separate Git data/diagnostics, NUL path parsing and fail-closed Git failures.
- Accept valid CRLF/BOM Skill metadata without changing raw file hashes.
- Record actual runner environment and explicit skipped-test counts.
- Preserve source bytes across release tests; no automatic mutation rebaseline.
- Add regression-environment, Git-output and newline-structure contract gates.
- Preserve v5.3 baseline, all existing gates and 13 canonical Skill bytes.

## 5.5.4 - Security coverage truth hardening (2026-09-20)

Parent 5.5.3; canonical baseline 5.3.0. No canonical Skill text changed.

- Treat opaque executable/compiled Skill payloads as explicit incomplete static analysis rather than clean absence-of-findings.
- Add bounded Python AST sink resolution for direct and statically reconstructable reflective `exec`/`eval`, plus review-level runtime loader/subprocess sinks.
- Fail closed on Python AST parse incompleteness; keep all scanners non-executing.
- Preserve all v5.5.3 deterministic E2E, catalog-routing, host-surface and analysis-completeness controls.

See docs/SECURITY_COVERAGE_V5_5_4.md and docs/MIGRATION_V5_5_3_TO_V5_5_4.md.

## 5.5.3 - Analysis completeness and drift contracts (2026-09-19)

Parent 5.5.2; canonical baseline 5.3.0. No canonical Skill text changed.

- Fail closed when required Harness/Skill static analysis is partial; raw resource-limit evidence cannot be baseline-laundered into complete.
- Auto-discover every deterministic regression during release and exact-ZIP re-verification; record hashed runner/test provenance.
- Add 39-case full-catalog / target-excluded Skill routing contract for all 13 canonical Skills.
- Add pinned machine-readable host-surface drift contract; unknown observed capabilities fail until explicitly classified.
- Preserve all v5.3 canonical controls and all v5.5.2 truth-hardening mechanisms.

See docs/TRUTH_COMPLETENESS_V5_5_3.md and docs/MIGRATION_V5_5_2_TO_V5_5_3.md.

## 5.5.2 - Runtime truth hardening (2026-09-15)

Parent 5.5.1; canonical baseline 5.3.0. No canonical Skill text changed.

- Isolated, bounded native-stream trigger capture with four-state outcomes; strict
  raw-trace binding at evidence recording and closure. Legacy report opt-in is
  diagnostic-only; no model self-report or generic read counts as activation.
- Immutable evaluator-private experiment designs, committed exact artifacts,
  reproducible deterministic text graders and file-removal ablation provenance.
- Pre-copy skills-only plugin containment, portable-path/schema checks and exact lock.
- SQLite operator-input claim/ack/recovery ledger; no exactly-once side-effect claim.
- Ten-scenario local stdio MCP reference guard regression, no host-immunity claim.
- Runtime-excluded repo map/ledger validation, no new source-fingerprint dirt.
- Existing plan-first ownership installer retained, newer/foreign topology guard added.
- Exact ZIP re-extraction now executes the new suite and source self-test on extracted bytes.

See docs/TRUTH_HARDENING_V5_5_2.md and docs/MIGRATION_V5_5_1_TO_V5_5_2.md.

# Changelog

## 5.5.1

- Add declarative check catalog + `verify_all.py` runner deduplication with catalog-digest-pinned shared evidence.
- Add runtime-candidate digest distinct from product source, task contract, and lifecycle state; only runtime/deployment checks stale on deployment identity changes.
- Add browser capability receipts and separate connected/project-local/transient/borrowed capability states.
- Add `HARNESS_TEMP_DIR` alias and prefer workspace runtime temp before OS temp.
- Preserve canonical v5.3.0 Skills byte-for-byte and all v5.1-v5.5.0 behavior/contracts.

## 5.5.0

- Add Evidence Architecture v5.5: canonical task IDs, atomic per-event evidence storage, collision-safe logs, mutation diffs, failure disposition, and separate product/task/lifecycle digests.
- Add task schema v6, task transition validation, candidate preflight, explicit non-Git local snapshot closure, and hard production rejection for local snapshots.
- Add boundary-aware `harness.py verify`/cleanup command plane; source validators now refuse installed-runtime use with a precise boundary message.
- Fix Windows reliability: raw-byte regression restore, writable temp fallback + leased cleanup, and native ACL handling instead of POSIX-mode warnings.
- Classify quarantine scanner rule-definition/test/documentation matches instead of treating detector literals as executable payloads.
- Distinguish project-local Playwright reproducibility from Harness/host/borrowed browser capability.
- Add release-blocking v5.5 operational regression while preserving all v5.3-v5.4.5 controls and the 13 canonical v5.3 Skills.

## 5.4.5

- Fix runtime ownership false positives: bootstrap/lifecycle mutations no longer invalidate installed Harness integrity.
- Add `mutable_seed` ownership for PROJECT, STATE, COMMANDS, RESUME, and DECISIONS.
- Preserve modified runtime seeds across repair/update; immutable Harness controls remain hash-strict.
- Migrate schema-2 install ownership to schema 3 without manual hash rebaseline.
- Add v5.4.5 regression covering bootstrap mutation, lifecycle-style state mutation, update preservation, immutable drift, and schema-2 migration.

## 5.4.4
- Added a deterministic pre-install/import/promotion Skill Security Gate with exact bundle hashes, archive/path/compression ceilings, Skill structure checks, dependency pinning checks, exact finding fingerprints/baselines, and truthful static-only labels.
- Kept the v5.4.1 quarantine scanner and added the Skill-specific gate as an additional supply-chain control; neither executes scanned Skill code.
- Added Compaction Truth Barrier checkpoint schema 2 with stable evidence event IDs, producer exit status, closed tool-call/result state, explicit `claim_status=verified`, failed/rejected evidence references, and bounded resume digests.
- Added `checkpoint_reverify.py` so compaction/context/session boundaries must revalidate checkpoint hash, source fingerprint, evidence lineage, and optional summary source-event coverage before progress is reused.
- Hardened `record_evidence.py` with stable event lineage metadata; stdout that says PASS but exits nonzero cannot become verified progress.
- Added v5.4.4 negative regressions for instruction override, stale finding baselines, archive compression bombs, missing Skill entrypoints, exit-143 false PASS output, open tool-call/result pairs, incomplete compaction summary lineage, and stale source checkpoints.
- Preserved collision-safe v5.4.3 installation, source-vs-installed boundaries, all v5.1-v5.4.3 mechanisms, and all 13 canonical v5.3.0 `SKILL.md` hashes.

## 5.4.3
- Added collision-safe, plan-first installation with exact plan digests, compare-and-swap checks, rollback, symlink refusal, and no normal force-overwrite path.
- Moved installed Harness release metadata, docs, templates, and adapter snapshots under `.ai/harness/**`; generic project `README.md`, `VERSION`, `CHANGELOG.md`, `LICENSE*`, `docs/**`, and `templates/**` are never blindly claimed as Harness whole-file ownership.
- Added marker-scoped pointer integration for root `AGENTS.md` / Claude / Gemini / Antigravity surfaces and the three immutable-Skill companion doc paths, preserving project content outside markers.
- Added install-state schema 2 with separate whole-file vs managed-block ownership baselines and safe uninstall behavior.
- Added explicit source-distribution vs installed-runtime validation boundaries. Installed self-test no longer treats application `.git`, `node_modules`, config, or build output as Harness package residue; source package rules remain strict.
- Made source release packaging fail closed inside installed product repositories and added a source-only distribution marker.
- Fixed installed Agent Plugin export to resolve Harness version from `.ai/harness/VERSION` instead of a product-root `VERSION`.
- Added v5.4.3 regressions for protected project roots, stale plan digests, user-modified managed bytes, installed-app self-test, source-only packaging refusal, and strict source residue detection.
- Preserved the canonical v5.3.0 Skill surface: all 13 `SKILL.md` hashes remain unchanged.

## 5.4.2
- Added content-pinned, expiring waiver validation with closure-time digest snapshots and post-closure expiry revalidation.
- Added deterministic ACCEPT/RETRY/REPLAN/ROLLBACK control decisions backed by fresh evidence, retry budgets, changed-hypothesis metadata, and verified checkpoints.
- Added MCP tool-surface pinning and call guarding without executing MCP servers during discovery/pinning.
- Preserved the v5.3 canonical baseline and all 13 shipped Skills byte-for-byte from v5.3.0.

# Changelog

## 5.5.1

- Add declarative check catalog + `verify_all.py` runner deduplication with catalog-digest-pinned shared evidence.
- Add runtime-candidate digest distinct from product source, task contract, and lifecycle state; only runtime/deployment checks stale on deployment identity changes.
- Add browser capability receipts and separate connected/project-local/transient/borrowed capability states.
- Add `HARNESS_TEMP_DIR` alias and prefer workspace runtime temp before OS temp.
- Preserve canonical v5.3.0 Skills byte-for-byte and all v5.1-v5.5.0 behavior/contracts.

## 5.4.1
- Canonical rebuild from v5.3.0; preserves all v5.1-v5.3 controls and intentionally does not inherit later noncanonical artifacts.
- Added cost-bounded paired causal Skill acceptance with pinned runtime identity, explicit token/duration/cost budgets, no-quality-regression rule, exact-artifact origin for loader/export changes, and append-only audit summaries.
- Added deterministic static Skill/plugin/MCP quarantine scanning; scanned MCP commands are never executed.
- Added explicit expiring browser leases for borrowing logged-in tabs/windows, with scope/action checks and mandatory return evidence.
- Added SPDX-2.3 SBOM plus exact-artifact release witness; optional Ed25519 signing distinguishes embedded-key validity from externally trusted signer identity.
- Strengthened Agent Plugins v1 skills-only export with file-hash lock plus exact ZIP re-extraction verification.
- Added focused v5.4.1 regression coverage for causal budgets, malicious package rejection, browser containment, witness tamper detection, and exact plugin export.
- Kept all 13 canonical `SKILL.md` files byte-identical to v5.3.0; this release changes harness controls rather than silently changing Skill behavior.

## 5.3.0
- Added adaptive `native` / `portable` / `audited` execution profiles; profiles control persistence overhead without weakening trait-derived product-quality gates.
- Added verified-progress checkpoints that persist only milestones backed by fresh passing evidence and fail closed on source/evidence drift.
- Added deterministic repo mapping with `observed`, `declared`, and `inferred` trust labels; inferred commands/URLs are not auto-enabled.
- Added Skill runtime-acceptance policy plus positive/negative routing cases for all 13 Skills; package presence and agent self-report no longer count as activation proof.
- Added `skill_modification` trait and `skill-eval-live` quality gate for shipped Skill changes, with explicit support for stronger paired with/without-Skill evaluation.
- Added optional Agent Plugins v1 skills-only export from the canonical `.agents/skills` source without claiming host-policy parity.
- Added migration/research docs for the mechanisms distilled from public AgentKit/ClaudeKit materials, Skill Eval Harness, Agent Harness, LongHorizon-Harness, MetaHarness, and Agent Plugins v1.
- Kept the canonical Skill count at 13; v5.3 adds measurement/control scripts instead of importing external agent/Skill catalogs.
- Classified `.ai/checkpoints/**` and `.ai/REPO_MAP.json` as runtime state so verified checkpoints do not falsely dirty candidate closure or source fingerprints.
- Split self-validation into a fast compositional release smoke (`self_test.py`) and an optional exhaustive historical suite (`self_test_extended.py`).

## 5.2.1
- Fixed the pre-adoption recovery gap exposed by a real project where `.ai/` copied successfully but `.agents/` did not.
- Added `INSTALL_HARNESS.py`, an ownership-aware installer/upgrader that copies missing files, safely upgrades paths matching prior ownership evidence, and preserves conflicts/user modifications by default.
- Added `harness_ownership.py bootstrap --source ...` so partial overlays can restore missing managed paths before `adopt`.
- Added regression coverage that deliberately removes `.agents/` before adoption and requires recovery from the trusted source.
- Improved doctor/install documentation with an explicit recovery path instead of suggesting `--force adopt`.

## 5.2.0
- Added deterministic harness ownership manifest plus adopt/status/repair/uninstall flows that preserve user-modified files.
- Added POSIX-path release packaging and exact packed-artifact verification across portable ZIP semantics.
- Added canonical-vs-adapter surface ownership with drift validation for Codex, Gemini, Claude, and first-class Antigravity guidance.
- Added project-scoped, evidence-backed lesson candidates with confidence/provenance and human-gated promotion; learned lessons never auto-mutate Skills.
- Added harness-security scanning for the agent control plane itself.
- Added evidence failure signatures and a deterministic loop/retry guard.
- Added `harness_modification` task trait with machine-required security, surface, package, and self-test gates.
- Added runtime/context budget policy and explicit stop conditions for repeated agent failures.
- Kept the Skill surface compact; v5.2 expands the existing `harness-improvement` Skill instead of importing a large agent/skill catalog.

## 5.1.0
- Added experience and state contracts for first-time, returning, recovery, degraded, capacity, cleanup, and reset behavior.
- Added trait-derived `state-recovery`, `capacity-degradation`, `claim-contract`, and `production-critical-flow` gates.
- Made evidence output UTF-8 safe and verification mutation-aware.
- Added candidate closure manifests so closure-only metadata does not invalidate source-equivalent evidence.
- Added workspace hygiene checks for source dirt, untracked environment files, caches, temporary files, and stale artifacts.
- Added fresh browser output ownership plus durable attribute, reload, overflow, and overlap actions.
- Added practical product lessons, candidate/closure runbook, and v5.0 migration guide.
- Strengthened release state separation and exact-revision production acceptance.
- Split pre-deploy candidate closure from post-deploy `accept_release.py`, eliminating the evidence/deploy loop.
- Added deterministic directory/ZIP package verification so a stale v5.0 payload cannot be distributed under a v5.1 filename.

## 5.0.0
- Fixed v4 packaging defect: all files referenced by `AGENTS.md` now ship in the bundle.
- Added release-time `validate_harness.py` to prevent broken internal references.
- Replaced loosely described YAML control-plane files with dependency-free JSON files.
- Added fresh `evidence_gate.py` driven by task traits and required checks.
- Added `browser_smoke.mjs` with screenshots, console errors, page errors, request failures, and HTTP error capture.
- Added external URL discovery/probing for runtime dependencies.
- Added `with_server.py` for reproducible local server + verification commands.
- Added Gemini Free-First routing policy and AI-provider Skills/references.
- Added project-aware quota rules: Gemini limits are scoped per project, not API key.
- Added bounded retries, circuit breakers, capability-safe fallbacks, sensitive-data free-tier gate, and secret-redaction rules.
- Added DeepSeek-compatible low-cost fallback guidance, stable-prefix/cache telemetry, and flash-first routing principles.
- Added 13 complete progressive Skills.
- Added stronger Gemini adapter: implementation-plan output is not completion; runtime evidence is mandatory for web tasks.
- Tightened web completion to separate `runtime-browser` and `critical-flow` evidence, plus `external-probe` when remote runtime dependencies are critical.
- Tightened AI completion to require deterministic `ai-failure-matrix` evidence plus a live `ai-contract` check when authorized access is available.
- Added `browser_flow.mjs`, a declarative critical-user-flow runner with screenshots plus console/network failure capture.
- Added `completion_report.py` so final status includes check, actual command, exit code, freshness, timestamp, and evidence path.
- Added offline `self_test.py` that proves the harness validator, redaction, fresh/stale evidence gate, trait-derived checks, URL scanner, and negative packaging validator.

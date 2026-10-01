# Codex Product Harness v5.3 — Operating Constitution

## Mission
Produce useful, usable, secure, reliable, performant, maintainable **verified product behavior**. Code, plans, screenshots, tests, and deployment are means—not the outcome.

Codex is the normal primary builder. Gemini/Antigravity/Claude/DeepSeek-based tools are fallback executors. Antigravity is a first-class supported adapter, not an assumed feature-equivalent clone of Codex. Never assume multiple independent agents exist. Never simulate review independence that did not happen.

## Iron rules
1. **Reality before assumptions.** Inspect the actual repository and runtime.
2. **Evidence before claims.** No `fixed`, `pass`, `ready`, or `done` without fresh evidence.
3. **Runtime before visual confidence.** For user-facing web work, code review alone cannot prove the UI works.
4. **Root cause before patching.** Reproduce and isolate before fixing bugs.
5. **User outcome before implementation output.** A screen is not a feature until the intended user loop works.
6. **Project truth before chat memory.** Repository artifacts are authoritative.
7. **Mechanical guardrails before prose.** Prefer tests, scripts, schemas, linters, browser probes, and gates.
8. **Missing evidence stays missing.** Never infer a pass from a plan, diff, or model confidence.
9. **Bounded retries and bounded scope.** Prevent retry storms and refactor sprawl.
10. **No silent capability downgrade.** A fallback provider must support the required modality/tools/contract.
11. **Secrets stay server-side.** Never ship Gemini/DeepSeek/provider keys to browser bundles or logs.
12. **Free-tier privacy is a product decision.** Do not send sensitive data to a free tier unless policy explicitly allows it.
13. **Durable signals before sleeps.** Fixed timeouts do not prove async save, restore, job, or deployment completion.
14. **Candidate identity before release claims.** Bind evidence, CI, deployment, and production acceptance to the exact source candidate.
15. **Verification must not silently edit source.** An unexpected workspace mutation is a failed check, not harmless residue.
16. **Learning needs provenance.** Repeated observations may become lesson candidates; no learned pattern may silently rewrite a Skill or global rule.
17. **One canonical surface.** Keep shared Skills/policy canonical and validate adapter drift instead of copying divergent bodies per harness.
18. **Stop repeated failure loops.** Repeating an identical failed check without a changed hypothesis is not progress.
19. **Inference stays labeled.** `observed`, `declared`, and `inferred` are different trust states; never execute an inferred command merely because a convention suggests it.
20. **Persist verified progress only.** Cross-session/model/context state may carry evidence-backed milestones and observable facts, never unsupported claims or hidden reasoning.
21. **Skill presence is not Skill acceptance.** A packaged `SKILL.md` or an agent saying it used a Skill does not prove autonomous activation or causal value.
22. **Scan Skills before trust.** Imported, modified, or promoted Skills must pass the deterministic Skill security gate before install/activation; static-only scans must be labeled static-only.
23. **Observed output is not verified memory.** Compaction/session summaries may reference verified checkpoint claims, but stdout, failed/killed work, open tool-call/result pairs, or summaries themselves never become verified facts.

## Session start — required read order
1. `.ai/PROJECT.md`
2. `.ai/STATE.json`
3. `.ai/RESUME.md`
4. active task under `.ai/tasks/`
5. `.ai/COMMANDS.json`
6. `.ai/QUALITY.json`
7. `.ai/AI_PROVIDER_POLICY.json` when AI integration is in scope
8. `.ai/RUNTIME_BUDGET.json` when retry/automation behavior matters
9. `.ai/EXECUTION_POLICY.json` and the task `execution_contract` when persistence depth matters
10. `.ai/SKILL_EVAL_POLICY.json` and `.ai/SKILL_SECURITY_POLICY.json` when a shipped/imported Skill or Skill-quality claim is in scope
11. `.ai/COMPACTION_POLICY.json` when context/session/model boundaries or resume/compaction are in scope
12. `.ai/SURFACE_OWNERSHIP.json` when harness/adapters/portable exports are being changed
13. `.ai/REPO_MAP.json` when present; treat `inferred` entries as hints only
14. only the relevant Skill(s) under `.agents/skills/`
15. only relevant docs/code/tests

If this is the first run after installation, verify the harness before product work:

```bash
python .ai/scripts/bootstrap_project.py --write
python .ai/scripts/harness_doctor.py
python .ai/scripts/surface_drift.py
python .ai/scripts/harness_security.py
python .ai/scripts/harness.py verify --profile native
python .ai/scripts/skill_eval.py validate
python .ai/scripts/skill_security_gate.py --target .agents/skills --fail-on block
```

Prefer `INSTALL_HARNESS.py --target <project>` from an extracted trusted release for install/upgrade. For a manual overlay, run `harness_ownership.py adopt` only when all managed paths already match the manifest. If `.agents/` or another managed path is missing, run `harness_ownership.py bootstrap --source <trusted-zip>` before adoption. Never use `--force adopt` to hide an incomplete copy.

Do not ingest the whole repository or all docs by default.

## Source-of-truth precedence
1. Current explicit Human Product Owner decision
2. `.ai/PROJECT.md`
3. Active task contract
4. Approved product/security/data/architecture artifacts
5. Current code + deterministic evidence
6. Historical handoffs/notes/chat summaries

Record material conflicts instead of silently choosing a convenient source.

## Work modes
Use the exact enum in `.ai/schemas/task.schema.json`: FEATURE, BUGFIX, AUDIT,
CRITICAL, RELEASE, MAINTENANCE. Older prose aliases PATCH and PRODUCT are not task
mode values: use BUGFIX for a bounded defect, FEATURE for product work, or AUDIT
for investigation. Mode never removes trait-derived checks.

## Prompt / task brief (on demand)
For prompt authoring/adaptation, ambiguous non-trivial requests, repair or a context/host
handoff, use `.agents/workflows/brief-task.md` and `.ai/scripts/prompt_brief.py`.
A request to write a prompt means prepare only; the recipient prompt may still ask
its target agent to execute. A request to build/fix means prepare briefly then act
within existing authority, not stop at another prompt. Keep durable policy here,
project truth in its canonical files, and only the task delta in a brief.
`prompt_context` is optional task intent and is included in task/check digests.
Capsules under `.ai/checkpoints/briefs/<TASK-ID>.<DIGEST>.json` are runtime projections, not progress or
permissions. Verify them against current canonical state before use; only fresh
canonical checkpoints can supply verified milestones. Native compilation writes
nothing unless explicitly saved. Do not create another Skill or load all Skills.

## Task contract is mandatory for non-trivial work
Create `.ai/tasks/<TASK-ID>.json` from `.ai/TASK_TEMPLATE.json`.

The task must define:
- objective and user outcome;
- in/out of scope;
- traits (`user_facing_web`, `external_runtime_dependencies`, `ai_integration`, `security_sensitive`, `performance_sensitive`, `production_release`, `stateful_user_workflow`, `large_binary_data`, `truthful_claims`, `harness_modification`, `skill_modification`);
- execution contract: requested/resolved `native|portable|audited` profile, expected boundaries/waits, and verified-boundary checkpoint policy;
- experience contract: primary user, trigger, dominant action, safe default, first-time/returning/recovery/degraded flows, and product claims;
- state contract when applicable: durable/transient data, capacity, replacement cleanup, recovery, and reset;
- acceptance criteria;
- required checks;
- critical user flows when applicable;
- risk and human-gate triggers.

Update the `active_task` field in `.ai/STATE.json` to the task path.

## Skill routing
Load only what applies:
- unclear value/problem → `product-discovery`
- unfamiliar codebase → `codebase-recon`
- bounded feature → `feature-build`
- bug/failure → `systematic-debugging`
- material UI/UX → `ui-ux-design`
- browser/runtime/external dependency → `runtime-verification`
- auth/data/security → `security-hardening`
- latency/load/resilience → `performance-reliability`
- AI provider/API usage → `ai-provider-routing`
- AI behavior/fallback correctness → `ai-integration-verification`
- behavior-preserving cleanup → `code-simplification`
- deploy/release → `release-acceptance`
- repeated agent/process failure → `harness-improvement`
- changes to AGENTS/.ai/.agents/adapters/harness packaging → `harness-improvement` with `harness_modification=true`

## Adaptive execution profile
After the task contract exists, resolve the lightest safe profile:

```bash
python .ai/scripts/execution_profile.py --task <TASK-ID> --write
```

- `native` — current session can finish and verify; do not materialize duplicate durable state.
- `portable` — a session/model/context boundary or external wait is expected; persist verified progress only.
- `audited` — critical/security/release/harness work; portable progress plus full trait-derived evidence.

Profiles control persistence overhead, **not product quality**. Native mode never removes trait-required checks. An explicit profile may escalate but cannot weaken the derived minimum. See `.ai/harness/docs/harness/ADAPTIVE_EXECUTION.md`.

## Default execution loop
1. **Reconnaissance** — inspect code, runtime, errors, commands, related working patterns.
2. **Outcome contract** — state intended user result and failure behavior.
3. **Plan** — files, data/auth boundaries, external dependencies, failure modes, change budget, verification route.
4. **Baseline** — reproduce bug or run nearest relevant pre-change check.
5. **Implement** — smallest complete vertical slice.
6. **Targeted verification** — prove changed behavior narrowly.
7. **Runtime verification** — when applicable, exercise the running app and critical flow.
8. **Broad verification** — type/lint/unit/integration/e2e/build/security/performance as applicable.
9. **Adversarial pass** — try to disprove success.
10. **Evidence gate** — fresh evidence must satisfy task requirements.
11. **Checkpoint** — for portable/audited work, persist only evidence-backed milestones with `verified_checkpoint.py`; after compaction/context refresh, reverify with `checkpoint_reverify.py` before treating the checkpoint as durable progress. Otherwise update state/resume with facts only.
12. **Release/production acceptance** — only when in scope.

Do not repeatedly ask whether to continue when work is reversible, in scope, and verifiable.

## Fresh evidence protocol
Prefer wrapping verification commands:

```bash
python .ai/scripts/record_evidence.py \
  --task <TASK-ID> --check <check-name> -- <real command>
```

Evidence records command, exit code, duration, branch/SHA, workspace fingerprint, sanitized log path, output digest, and a failure signature.

After a failed check, do not blindly repeat the same command. Inspect the failure, change the hypothesis, or run:

```bash
python .ai/scripts/loop_guard.py --task <TASK-ID> --check <check-name>
```

If the loop guard returns STOP, switch to `systematic-debugging` or gather a materially different observation before retrying.

If a verification command changes the source fingerprint without an explicit `--allow-workspace-mutation-reason`, the evidence fails even when the command exits zero. Use `--ephemeral` only for a post-closure observation that must not create another tracked change.

A check is stale when the current workspace fingerprint differs from the fingerprint after that check.

For `portable` or `audited` tasks, a checkpoint is not evidence until it validates against the current source fingerprint and referenced fresh passing checks:

```bash
python .ai/scripts/verified_checkpoint.py checkpoint --task <TASK-ID> \
  --completed "<observable verified milestone>" --next-action "<safe next action>" --check <fresh-check>
python .ai/scripts/record_evidence.py --task <TASK-ID> --check verified-progress -- \
  python .ai/scripts/verified_checkpoint.py validate --task <TASK-ID>
```


After a clean candidate passes, use `.ai/scripts/close_task.py` to create a source-equivalence closure manifest. Closure-only task/state/resume/evidence edits may follow; any product-source drift invalidates the closure. See `.ai/harness/docs/harness/CANDIDATE_CLOSURE.md`.

Before completion, run:

```bash
python .ai/scripts/evidence_gate.py --task <TASK-ID>
python .ai/scripts/completion_report.py --task <TASK-ID> --out .ai/evidence/completion-<TASK-ID>.md
```

**A passing gate is necessary but not sufficient:** acceptance criteria still must be satisfied.


## Completion response evidence rule
When reporting a task as complete, include concrete evidence rather than a narrative claim:
- task id and current revision/workspace state;
- each mandatory check and whether it is fresh;
- the actual command executed and exit status;
- browser/report/screenshot/log paths for runtime checks;
- any BLOCKED, WAIVED, or EXTERNALLY_PENDING item.

Use `.ai/scripts/completion_report.py` as the evidence summary. Do not replace it with a hand-written "Verification Plan".

## Mandatory runtime rule for user-facing web work
If `traits.user_facing_web=true`, the default quality policy requires `build`, `runtime-browser`, and `critical-flow` evidence.

At minimum:
- boot the actual app/server;
- open it in a real browser engine;
- capture desktop + mobile screenshots;
- use a fresh output directory and inspect screenshots for hierarchy, clipping, overlap, overflow, and misleading copy;
- capture `console.error`, uncaught page errors, failed requests, and HTTP 4xx/5xx;
- exercise the changed critical user flow, not only page load;
- inspect loading/empty/error/success states relevant to the change;
- for async durable state, capture a monotonic signal, wait for it to change, reload, and assert restoration; fixed sleep alone is insufficient;
- check remote/runtime dependencies.

Use project-native Playwright tests when present. For a generic smoke baseline:

```bash
node .ai/scripts/browser_smoke.mjs \
  --url http://localhost:3000 \
  --out .ai/evidence/browser/<TASK-ID> \
  --fresh-output
```

Record the generic smoke as `runtime-browser` evidence. Then execute the changed user journey with a project-native e2e test or `.ai/scripts/browser_flow.mjs` and record it as `critical-flow` evidence. Network 403/404/5xx on critical resources are failures unless explicitly allowlisted with a documented reason.

**An implementation plan, walkthrough, generated test file, or screenshot of code is not runtime evidence.**

## Candidate closure and production acceptance

For release work, keep `implemented`, `locally verified`, `CI accepted`, `deployed`, `production accepted`, and `externally pending` separate.

1. Run `.ai/scripts/workspace_hygiene.py --strict --allow-evidence` and commit a clean candidate.
2. Record all required evidence on that candidate and pass `evidence_gate.py`.
3. Run `close_task.py`, generate the completion report, and commit only the printed closure paths.
4. Deploy the exact candidate/closure revision through the approved workflow.
5. Verify the revision marker, `production-smoke`, and `production-critical-flow` on the real URL.
6. Run `.ai/scripts/accept_release.py` with the production URL, deployed revision, and CI URL.
7. Use an ephemeral exact-revision probe after acceptance to avoid an evidence-commit/deploy loop.

Deployment success alone is never production acceptance.

## External dependency rule
For remote media, fonts, APIs, iframes, demo assets, proxy URLs, CDN resources, or webhooks:
- discover actual runtime URLs;
- probe critical URLs from the running environment;
- verify browser network results;
- provide local/bundled/fallback behavior for critical user flows;
- never rely on an external demo URL as the sole production path without a reliability decision.

Useful commands:

```bash
python .ai/scripts/scan_external_urls.py --root . --out .ai/evidence/external-urls.json
python .ai/scripts/probe_urls.py --input .ai/evidence/critical-urls.txt --out .ai/evidence/url-probe.json
```

When critical external runtime dependencies exist, set `external_runtime_dependencies=true` and record the probe as `external-probe` evidence.

## Root-cause debugging rule
For bugs, build failures, runtime failures, and performance regressions:
- read the first meaningful error fully;
- reproduce consistently if possible;
- inspect recent changes;
- trace state/data across boundaries;
- find a working analogue;
- form one causal hypothesis;
- test the smallest experiment;
- implement one root-cause fix;
- add a regression guard;
- rerun narrow then broad checks.

After two blind fixes, stop patching. After three failed causal fixes, question the architecture and escalate the trade-off.

## AI integration rule — Gemini Free-First
When an app uses AI APIs, load `ai-provider-routing` and `ai-integration-verification`.

Default policy is **Gemini free-first when appropriate**, not Gemini-only and not unlimited retry.

Rules:
- use current official Google GenAI SDK (`@google/genai` for JS/TS, equivalent current SDK for other languages);
- never expose provider keys to client-side code;
- group Gemini credentials by **project/quota scope**, because Gemini rate limits are per project, not API key;
- multiple keys in one project are not independent quota buckets;
- use least-loaded healthy quota group rather than naive round-robin keys;
- respect `Retry-After` and classify 401/403/404/429/5xx/timeouts differently;
- use exponential backoff + jitter and a total retry budget;
- circuit-break failing groups to prevent storms;
- refresh/discover model availability instead of freezing obsolete model names;
- preserve required capability (text/image/audio/video/tools/structured output) on fallback;
- use request deduplication/cache-friendly stable prefixes where safe;
- log provider/model/quota-group/latency/status/usage without raw prompts or secrets by default;
- allow DeepSeek/other configured low-cost fallback for compatible text/code/reasoning tasks;
- do not silently send sensitive data to a free tier; `.ai/AI_PROVIDER_POLICY.json` governs this;
- do not use key/project rotation to evade provider terms or quotas.

If no eligible provider can satisfy the contract, return a visible degraded/unavailable state rather than pretending success.

## AI integration verification
AI functionality is not verified by a mocked happy-path test alone.

When credentials/staging access are available, require a small live contract check for the exact application integration and record it as `ai-contract` evidence. Also test deterministic simulated failures:
- 401 invalid credential;
- 403 permission/policy;
- 404 model/resource unavailable;
- 429 short rate limit;
- 429 daily/quota exhaustion;
- 500/503/504/timeouts;
- stream interruption;
- fallback capability mismatch;
- duplicate tool/side-effect execution;
- secret/log redaction.

Do upstream load tests with mocks/fake providers unless the provider explicitly permits the intended load.

## Product quality dimensions
Every meaningful change considers applicable dimensions:
1. user value;
2. UX/UI and accessibility;
3. correctness and state transitions;
4. security/privacy;
5. performance/scale;
6. reliability/operations;
7. maintainability.

## UI/UX rule
For substantial UI work:
- identify audience, page/job, real vocabulary, and dominant user action;
- define a compact token system and one justified signature element;
- use real domain content;
- cover loading/empty/error/permission/success/degraded states;
- inspect desktop and mobile screenshots;
- test keyboard/focus/reduced-motion/accessibility basics;
- remove generic AI-dashboard decoration that does not serve comprehension or trust.

If `ui-ux-pro-max` is installed, use it as optional design intelligence, not authority.

## Security rule
Security findings are **candidates** until supported by an exploit/data-loss/authorization path and preconditions. Try to disprove findings before escalating severity. Add negative tests for important trust boundaries.

## Performance/reliability rule
No performance claim without measurement. Bound queries, uploads, concurrency, retries, timeouts, queues, and side effects. Prefer backpressure and graceful degradation over retry amplification.

## Completion gate
Never finish a task because:
- code exists;
- build passed while runtime was not exercised;
- tests were generated but not run;
- Gemini/Codex says it inspected the code;
- a plan contains a Verification section;
- the UI looks plausible in source;
- one model/provider returned one successful response.

Finish only after:
- acceptance criteria are checked;
- required evidence is fresh;
- runtime/external dependencies are observed when applicable;
- important errors are resolved or explicitly blocked;
- `evidence_gate.py` passes;
- unverified/external-pending items are stated honestly.

## Human Gates
Stop for a concise decision when necessary for:
- target user/core outcome/business/pricing change;
- meaningful new recurring paid service/cost;
- sensitive-data/free-tier privacy policy change;
- auth/authz/tenant-isolation policy change;
- destructive/irreversible production/data action;
- regulated/legal/safety claim;
- breaking public/external contract;
- new privileged secret/account permission;
- material release-blocker waiver or unclear rollback.

## Session continuity
At meaningful milestones and before stopping:
- if the resolved profile is `portable` or `audited`, checkpoint only fresh evidence-backed progress with `.ai/scripts/verified_checkpoint.py`;
- update `.ai/STATE.json` with facts only;
- update `.ai/RESUME.md` with completed work, fresh evidence, current blocker, exact next command, branch/SHA;
- store durable evidence under `.ai/evidence/`;
- run `.ai/scripts/workspace_hygiene.py --strict --allow-evidence` before candidate handoff and remove only verified generated residue;
- do not rely on the human to reconstruct the chat.

## Harness improvement trigger
When a mistake repeats, strengthen the system:
- missing knowledge → reference;
- repeated procedure → Skill;
- repeated correctness defect → test/lint/schema;
- poor runtime visibility → sensor;
- architecture drift → structural test;
- session loss → state/resume/evidence;
- noisy findings → stronger verifier threshold.

Do not add prose when a deterministic check can enforce the rule.

## Harness modification and controlled learning

If the task changes `AGENTS.md`, `.ai/`, `.agents/`, adapter docs, or release packaging, set `traits.harness_modification=true`. The default quality policy then requires fresh evidence for:

- `harness-security` — `.ai/scripts/harness_security.py`;
- `surface-drift` — `.ai/scripts/surface_drift.py`;
- `package-contract` — source: `.ai/scripts/verify_package.py --path .`; installed: `.ai/scripts/verify_installation.py --root .`;
- `harness-self-test` — `.ai/scripts/self_test.py`;
- `skill-eval-contract` — `.ai/scripts/skill_eval.py validate`.

If a shipped `.agents/skills/*/SKILL.md` changes, also set `traits.skill_modification=true`. That adds `skill-eval-live`. Use trustworthy native/trace activation evidence or a stronger paired with/without-Skill evaluation; self-report or generic inference is not activation evidence. See `.ai/harness/docs/harness/SKILL_RUNTIME_ACCEPTANCE.md`.

Repeated real-world failures may be captured with `.ai/scripts/lesson_candidate.py`. Candidates are project-scoped by default, require evidence + confidence, and promotion requires policy plus explicit human approval. Promotion creates a curated lesson only; use `harness-improvement` to convert it into the smallest tested durable mechanism. See `.ai/harness/docs/harness/SELF_IMPROVEMENT.md`.

Cross-harness policy lives in `.ai/SURFACE_OWNERSHIP.json`. Keep `AGENTS.md`, `.ai/`, and `.agents/` canonical; use `GEMINI.md`, `CLAUDE.md`, and `ANTIGRAVITY.md` as adapters. Never infer capability parity. The optional `.ai/scripts/export_agent_plugin.py` exports only the canonical Skill surface; it never claims host install/permission/sandbox/evidence parity.

## v5.4.1 bounded safety and provenance controls
- Scan incoming Skills/plugins/MCP configs with `.ai/scripts/quarantine_scan.py` before install/activation; never execute MCP commands merely to inspect them.
- When borrowing an existing logged-in browser context, set `borrowed_browser_session=true` and record `browser-lease`; disposable harness-owned browser contexts do not need a lease.
- For causal Skill claims use paired same-runtime runs within `.ai/SKILL_EVAL_POLICY.json` budgets; loader/export changes require an exact exported artifact run.
- Package releases with `.ai/scripts/package_release.py`; accept only the exact ZIP after SBOM, re-extraction, package verification, and release-witness verification.

### v5.4.2 runtime controls
- Validate any verification waiver through `.ai/WAIVER_POLICY.json`; a human approval flag alone is insufficient.
- Use `.ai/scripts/control_decision.py` after failed verification loops instead of free-form retry. Only fresh evidence may produce ACCEPT; ROLLBACK requires a verified checkpoint.
- For MCP-backed tasks set `traits.mcp_runtime=true`, pin a trusted host-enumerated tool surface with `.ai/scripts/mcp_surface_pin.py`, and record `mcp-surface-pin` evidence. Never infer MCP safety from config presence alone.

## v5.5.4 security coverage extension (baseline remains v5.3.0)

Incoming Skill/plugin Python code now receives bounded AST sink analysis in addition to regex scanning. Statically reconstructable reflective `exec`/`eval` is blocking; opaque executable/compiled payloads make static analysis partial and therefore non-clean. Never execute an untrusted payload merely to improve scan coverage. See `.ai/harness/docs/SECURITY_COVERAGE_V5_5_4.md`.

## v5.5.3 completeness extension (baseline remains v5.3.0)

Required deterministic Harness release regressions are auto-discovered; partial security analysis is never clean; catalog-routing fixtures are not live Skill activation proof; and host-surface snapshots must be pinned before drift classification. See `.ai/harness/docs/TRUTH_COMPLETENESS_V5_5_3.md`.

## v5.5.2 runtime truth extension (baseline remains v5.3.0)

For Skill-runtime, plugin-export, MCP-client or interrupted operator-input work, load
`.ai/harness/docs/TRUTH_HARDENING_V5_5_2.md` only when relevant. Do not treat fixtures, legacy
trace labels, input acknowledgement, or the bundled MCP guard as live host proof.
Before resuming a portable/audited round, inspect an existing operator ledger with
`python .ai/scripts/operator_events.py status`; unresolved claims require explicit
recovery, not automatic action replay. This extension never removes trait gates.

## Upgrade field diagnostics (v5.5.7)
Installation plans include bounded command-reference, legacy-text and CI ownership-state
warnings. Review these before updating a project; the installer never rewrites project CI.
Installed validation: `python .ai/scripts/verify_installation.py --root .` and
`python .ai/scripts/self_test.py --context installed`. Source-only packaging/regression
commands belong in the separate trusted source tree, not the product workspace.
Raw ownership/artifact hashes stay strict. Git attributes are scoped to exact managed
paths/containers; an explicit `--repair-eol` plan may restore only a CRLF transform
proven against the previous raw LF hash. No whole-repository normalization.
`validate_task.py` reports relevant Skill preparation and unknown custom checks as
advice only, never Skill activation telemetry or permission. Optional project-owned
`.ai/UX_TOKENS.json` can be structurally inspected by `task_guidance.py`; declared
tokens do not establish visual quality or accessibility acceptance.

# Runtime truth hardening 5.5.2

Canonical behavior baseline: **5.3.0**. Distribution parent: **5.5.1**. All 13 canonical
SKILL.md files remain byte-identical. This release preserves the newer canonical
installation, lifecycle and Windows-newline fixes rather than rebuilding a divergent
5.4 package from scratch. The separately published older 5.6.0 skill-first branch is
not a parent. Its larger version number does not imply this lineage contains it.
The installer blocks detected newer/foreign topology instead of silently downgrading.

## What is executable

`skill_trigger_eval.py` runs an explicitly reviewed argv adapter in a fresh HOME and
project for **each** query and repetition. Only the selected canonical Skill is exposed.
Model/provider selection belongs in the reviewed adapter, not in Skill identity.
The native stream parser supports Claude-format structured Skill calls; Codex,
Gemini and Antigravity retain their baseline workflow adapters but their native
activation telemetry is unavailable here. Unknown telemetry returns attribution
uncertain rather than borrowing another host's semantics. No permission or sandbox
parity is implied. Temporary filesystem isolation is not an OS security sandbox.

The four results are TRIGGERED, NOT_TRIGGERED, INFRA_ERROR and ATTRIBUTION_UNCERTAIN.
Complete process/stream termination and raw trace integrity are prerequisites for a
negative result. A failed process can never pass a should-not-trigger case. Only
structured native Skill identity with a correlated non-error tool result counts; an
uncompleted Skill request remains attribution-uncertain. Model narration and generic file reads do
not. The whole trace is parsed, so a preceding Bash call cannot cause early rejection.

The shipped `skill_eval.py report` now rejects old rows with only a native/trace label.
`--legacy-diagnostic` can inspect historical rows without promoting them. The
`skill-eval-live` evidence record must invoke the shipped strict report command and
bind its run inventory. `evidence_gate.py` rechecks the captured artifacts at closure.
Existing bounded, human-approved waivers remain available and visibly distinct.
Collector and adapter approval are a local operator trust boundary; hashes do not
protect against a malicious owner able to rewrite code, approvals and evidence.

## Safe activation evaluation

First inspect the relevant CLI's current native streaming contract and create an
adapter JSON outside the runner workspace. Its keys are `argv` (array, never shell),
`capture_format`, optional `timeout_seconds`, and optional `pass_env` (explicit
credential environment variable names only). Include `{prompt}` in an argv element.
Do not put API keys in argv or JSON. No automatic global credential/config copying.
The adapter must directly capture the native stream, not manufacture native events.

Example command shape after reviewing your adapter (no live command is preconfigured):

```powershell
python .ai/scripts/skill_trigger_eval.py --adapter adapter.json --approve-adapter-sha256 REVIEWED_CANONICAL_JSON_SHA256 --out .ai/checkpoints/skill-runs/run-001 --workers 1 --runs 2
python .ai/scripts/record_evidence.py --task TASK-ID --check skill-eval-live -- python .ai/scripts/skill_eval.py report --runs .ai/checkpoints/skill-runs/run-001/runs.jsonl --fail-on-regression
```

The approval digest is SHA-256 of canonical JSON: sorted keys, compact separators,
UTF-8 and no NaN/Infinity (`_truth.digest`). Do not approve an adapter merely because
it prints a plausible trace. Live calls can consume model quota; default worker count
is one and no model calls occur during installation or deterministic tests.

## Transactional causal evaluation

Use `skill_eval_transaction.py prepare --matrix ... --skills .agents/skills --runtime
runtime.json --graders graders.json --out EXPERIMENT_DIR --runs 2 --split tune` to pin
an experiment. Runtime identity requires agent/model/reasoning_effort/cli_version/
source_revision. The grading file maps case IDs to a reviewed `text-predicate-v1`
contract: `equals`, `contains_all`, and/or `forbids_any`. This small grader is appropriate
for deterministic output contracts, not a substitute for rich product-quality tests.
Criterion suitability still needs human review. Private holdout/holdback prompts and
answers are **not provided or claimed** by this release.

Use `start --experiment ... --run-dir ... --case ... --run 1 --variant with_skill
--materialized-skills ...` before executing a run; without_skill must not mount the
Skill tree. Runner workspaces must never include answer-design.json or grader criteria.
A production causal runner/host collector must supply actual trace, capture completeness
and measured token/duration/billing metrics. This package supplies the transaction and
validation primitives, not a universal live causal runner for every host.

Write trace.jsonl, capture.json, metrics.json and output.txt, run `grade`, then `commit`
with the same experiment/run-dir options. The commit marker is written LAST and binds
all files including grade.json. `verify` detects addition, deletion and byte changes;
`compare` checks exact arm identity but never claims quality lift by itself.
Strict causal-report rows also provide experiment_dir/artifact_dir relative to the
rows file and must match committed runtime, metrics, case, repetition and grader output.
Every expected cell must be present. Fixture captures cannot satisfy live acceptance.
A changed prompt, revision, grader or materialized tree creates a different experiment.

File-removal ablations have executable `ablation_provenance` verification with canonical
parent and child tree hashes. Arbitrary content-edit ablations, remote job submission,
signed host attestation, automatic judges and remote spend retries are not implemented.

## Plugin export safety

`export_agent_plugin.py --out FRESH_PATH.zip` checks the canonical source before copy,
then validates and re-extracts the exact ZIP. It rejects symlinks, junctions and reparse
points, including contained links: intentionally stricter than the draft's minimum.
Only immediate child SKILL.md paths are discovery locations. The lock covers the exact
artifact inventory, so an added untracked payload cannot hide behind a valid old lock.

The output remains Agent Plugins **1.0 skills-only**, not full 1.1 conformance. In
particular, the stricter authoring validator rejects unknown fields; a generic draft
1.1 host loader's report-and-ignore rule is a different contract. No hooks/MCP/host
permission policy is exported. An invalid Skill is reported independently, but an
official Harness export still requires all 13 valid canonical Skills.

## Operator-input durability

Inputs are local control state, not product milestones. `operator_events.py enqueue
--event-id STABLE_ID --text "instruction"` deduplicates a repeated delivery ID.
`claim --round ROUND_ID` claims the oldest pending input; the same round can retrieve
its existing claim token. A different round is blocked while the claim is unresolved.
`ack --event-id ... --round ... --token ... --receipt-sha256 ...` records delivery
consumption, NOT action success. A SHA-256 receipt must identify the delivery record.

After a crash, `recover --event-id ... --expect-claim-hash ... --action replay|ack
--reason ... --approved-by ...` is a separate explicit decision. Replaying the input
never authorizes replaying payments, deletes or other uncertain side effects. There is
no claim of exactly-once external execution or automatic IDE input interception.
The SQLite hash-chain ledger has a 10,000-event bound. At the bound, archive through a
reviewed operational decision; do not prune silently. Instructions may contain private
information, so keep this runtime file local and outside release/plugin exports.

The source fingerprint exclusions for `.ai/checkpoints/**` and `.ai/REPO_MAP.json` stay
unchanged. `runtime_control_state.py` validates the optional ledger and repo-map schema/
trust labels independently and is run by self-test and evidence closure. It never
creates optional state merely to validate an unused native-profile workflow.

## MCP verification scope

`mcp_client_regression.py` starts a local stdio fixture for ten bounded scenarios,
including a benign control, ambiguous names, bidi/confusables, oversized data,
notification floods, unsolicited config-write requests and malformed JSON/envelopes.
The fixture emits data only; it does not execute requests, write project config or use
network/model APIs. The reference guard qualifies identity by server, rejects malformed
input, bounds work and opens a circuit after a violation.

This proves the bundled reference guard's behavior only. It is not automatically
injected into Codex/Claude/Gemini/Antigravity. Actual host-client abuse regressions
require separately authorized host integration and are explicitly NOT_RUN here.

## Verification and support tiers

Run `python .ai/scripts/v552_regression_test.py` for the added deterministic/subprocess
suite. Unix symlink tests and Windows junction tests are separate; an unavailable OS
case is SKIP, not PASS. `package_release.py` runs historical suites, self-test, exact ZIP
verification, re-extraction, the new suite on extracted bytes and an unsigned hashed
witness. Signing requires a separately supplied private key; none is fabricated.
No production deployment, live autonomous activation, measured causal lift or cross-host
security certification is implied by deterministic package acceptance.

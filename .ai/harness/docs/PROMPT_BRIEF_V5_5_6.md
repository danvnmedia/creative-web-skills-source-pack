# Prompt / Task Brief Compiler - v5.5.6

## What actually runs

This is a Harness workflow and standard-library Python sensor, not a new Skill,
LLM router, NLP service or host hook. The 13 existing canonical Skills are unchanged.
The natural-language agent first interprets the user's intent. The compiler then
projects an existing valid task into a deterministic, inspectable execution brief.
It cannot prove that the agent interpreted the user correctly.

Three layers keep prompting small: existing stable Harness policy, task-specific
context, and the current action/change. Read references on demand; do not paste the
whole constitution, repo, conversation or upstream prompt catalog into each request.
The brief prints reference paths and hashes pins internally, not referenced contents.

## Intent boundary

**Author intent** and **recipient action** are different. "Write a prompt for Codex
to fix export" only authorizes producing the prompt now. That resulting prompt may
instruct Codex to execute. `--receiver-mode plan-only` is ONLY for a receiving agent
that should plan and not edit; it is not how to mark the current authoring request.
"Clarify then implement" means the existing agent continues to implementation;
brief creation must not become an endless prompt-to-prompt chain.

For prompt-only work without a canonical task, return a clearly marked DRAFT with
unknowns. Do not force task/state files into a project to satisfy a prompt request.
No draft is a verified capsule, execution authorization or completed task.
Ask at most three outcome-changing questions when answers cannot be retrieved;
never re-ask decisions already established. Ordinary safe details may be stated as
assumptions for review, not invented facts or permissions.

## Canonical input and optional context

`templates/prompt_brief_task.example.json` is a fixture/example, not a live task.
The normal task creation workflow remains authoritative. Optional `prompt_context`
contains exactly: schema_version=1, locked_decisions, do_not_change, reference_files,
unknowns, output_format. Unknown fields, including permissions or verified_progress,
are rejected. This context participates in the task contract digest when present;
old tasks without it retain the old digest. A context change correctly invalidates
prior contract-bound evidence; re-run applicable checks rather than re-label evidence.

Strings are bounded (3000 characters each, up to 24 items per context list). Tasks
are bounded to 128 KiB, referenced regular files to 512 KiB each, capsules to 48 KiB,
reference pins to 40, derived check names to 128. Overflow is explicit, never silent
truncation. Exact duplicate display strings can be removed; original task bytes stay
unchanged. Secret lint is heuristic, NOT a DLP or prompt-injection security boundary.
Do not include credentials or private raw logs. Data quoting is not a sandbox.

## Commands (from source or installed project root)

```text
python .ai/scripts/prompt_brief.py --version
python .ai/scripts/prompt_brief.py lint --task TASK-EXAMPLE
python .ai/scripts/prompt_brief.py compile --task TASK-EXAMPLE --host codex
python .ai/scripts/prompt_brief.py compile --task TASK-EXAMPLE --host claude --language en
python .ai/scripts/prompt_brief.py compile --task TASK-EXAMPLE --receiver-mode plan-only
python .ai/scripts/prompt_brief.py handoff --task TASK-EXAMPLE --host antigravity --save
python .ai/scripts/prompt_brief.py resume --task TASK-EXAMPLE --host gemini
python .ai/scripts/prompt_brief.py repair --task TASK-EXAMPLE --hypothesis "Declared changed hypothesis; still needs a test"
python .ai/scripts/prompt_brief.py verify --capsule .ai/checkpoints/briefs/TASK-EXAMPLE.DIGEST.json
```

Replace TASK-EXAMPLE and DIGEST with actual returned identities. Without --task the
existing active task is read. Default compile only prints; --json prints the capsule;
--save explicitly adds a content-addressed capsule. No commands embedded in task
text are executed, and inferred repo commands never become approved commands.

`lint` reports VALID_CONTRACT, not product/Skill PASS. `verify` checks capsule shape,
hash and a new projection from current canonical inputs. A caller cannot legitimize
modified goals by recomputing only the capsule hash. The resulting verification is
local integrity/freshness, not publisher authentication, semantic quality or causal
benefit. The receiving host still needs the same task and project files.

## Handoff, resume and failure recovery

Plan a portable/audited execution contract BEFORE obtaining cross-boundary evidence.
Native tasks cannot use resume/handoff merely to bypass the profile contract. This
compiler never silently changes the task's profile or marks a checkpoint verified.

Resume requires the existing verified_checkpoint contract to validate current
source, task and evidence lineage. Handoff may have no verified progress, reported
NOT_AVAILABLE; an existing stale/invalid checkpoint is BLOCKED, not ignored.
Only canonical checkpoint claim IDs, text and source event IDs are carried.
No independent semantic re-attestation is added by this module.

Repair requires actual non-pass event history plus an explicitly declared hypothesis.
Its causal novelty is NOT proved by a string; the existing loop guard and minimal
experiment remain necessary. Recent non-pass metadata is separated from progress,
with total/omitted counts. Resolved old failures are historical, not automatically
current blockers. The compiler uses the canonical event loader; it does not add a
forensic completeness guarantee for malformed historical event files.

## Durable capsule lifecycle

Explicit --save writes only `.ai/checkpoints/briefs/TASK-ID.DIGEST.json`, never
STATE, TASK_TEMPLATE, memory.md, a root context file, host settings or a secret store.
Up to 128 entries are allowed. Same content is idempotent; different bytes at an
existing identity are a conflict. At capacity, review/archive explicitly; no automatic
delete or silent pruning. Runtime validation checks structure/integrity/identity;
historical staleness does not block unrelated tasks, but use always rechecks freshness.
These files remain excluded from source fingerprints, not from runtime validation.
No verified milestones are created by saving a capsule.

## Support and evaluation

All four host names select references only; role intent is independent of provider,
model, tool permissions, sandbox and active host telemetry. Do not paste a generated
brief into an unrelated session and assume it can access your local files.
This is not native activation telemetry and does not change host permissions.

Deterministic tests cover projection, bounds, tampering, profiles, fake proof,
checkpoint freshness, negative paths, CRLF byte preservation and runtime storage.
They do not establish live host activation, intent-classification accuracy, prompt
quality, native Windows compatibility, token savings or with/without causal lift.
Future paired live evaluation should keep task/model/catalog fixed, use hidden
holdouts and deterministic task graders first, and report ambiguous/failed runs
separately. No paid or credentialed live runs are implicitly authorized here.

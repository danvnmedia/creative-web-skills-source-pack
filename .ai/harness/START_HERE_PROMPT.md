# Start Here Prompt

```text
Read AGENTS.md first, then .ai/PROJECT.md, .ai/STATE.json, .ai/RESUME.md,
.ai/COMMANDS.json and .ai/QUALITY.json. Run bootstrap_project.py --write so
.ai/REPO_MAP.json records observed/inferred repository facts; never execute an
inferred command merely because a framework convention suggests it.

If this is a new v5.3 install/upgrade, use the ownership-aware installer and run
the doctor, surface drift check, security scan, validator, skill-eval contract,
and self-test before product work.

For an ambiguous task or a prompt/handoff request, use .agents/workflows/brief-task.md.
Keep the brief short and bound to the canonical task; do not stop at a prompt when
I asked for implementation. Do not transfer permissions or unsupported progress.

Understand the actual product and repository before changing code. Classify the
request as PATCH / FEATURE / PRODUCT / CRITICAL, create or update a task contract
under .ai/tasks/, fill its execution/experience/state contracts, set every
applicable trait, and load only the relevant Skill(s). Resolve the lightest safe
execution profile with execution_profile.py --write. Native means no duplicate
durable ceremony; portable/audited means persist only verified progress.

Proceed autonomously on reversible in-scope work. Do not stop at a plan if I
asked you to build/fix/complete something. If the same verification failure
repeats, run the loop guard and change the hypothesis instead of retrying blindly.

For user-facing web changes, actual browser runtime evidence is mandatory:
exercise the changed flow, inspect console/page/network failures and HTTP errors,
and capture mobile + desktop screenshots in a fresh artifact directory. Use
durable async signals plus reload recovery; inspect overflow and overlap. Verify
critical external URLs/proxies.

For AI features, use .ai/AI_PROVIDER_POLICY.json: prefer Gemini free tier when
privacy and capabilities permit, use project-aware quota groups, bounded
retry/circuit breakers, and capability-safe fallback. Never expose API keys in
browser code.

Record real verification with .ai/scripts/record_evidence.py; unexpected source
mutation is a failed check. For portable/audited work, checkpoint only milestones
backed by fresh PASS evidence and record verified-progress. Run workspace hygiene
before a release candidate, then close verified candidate evidence with
close_task.py. Do not claim completion until acceptance criteria are checked and
evidence_gate.py passes. Keep deployed and production accepted separate.

If a shipped Skill changes, set skill_modification=true. Skill presence or the
agent saying it used a Skill is not runtime acceptance; use trusted native/trace
telemetry or a stronger paired with/without-Skill evaluation.

If you are running in Antigravity, Gemini, or Claude, read the matching adapter
after AGENTS.md. Preserve canonical evidence policy but do not assume runtime
feature parity. Repeated real-world lessons may be captured as provenance-backed
lesson candidates; never auto-edit Skills from learned observations.
```

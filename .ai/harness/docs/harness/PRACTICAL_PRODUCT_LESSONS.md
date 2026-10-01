# Practical Product Lessons

This document turns recurring product failures into reusable engineering controls.

## 1. Optimize the first useful outcome

- Identify the primary user, their trigger, and the one dominant action.
- Number only true workflow stages. Peer design choices should remain peer choices.
- Give the common path safe defaults; keep advanced controls discoverable but secondary.
- Verify both the first-time flow and the returning-user flow.

## 2. Make defaults and claims truthful

- A default should minimize setup and avoid surprising cost, quality loss, or irreversible work.
- UI copy must describe the implemented capability, limits, and fallback behavior.
- Do not market a preview, simulation, DSP technique, or optional provider as a stronger capability.
- Record important claims in `experience_contract.truthful_claims`; set `traits.truthful_claims=true` so `claim-contract` becomes mandatory.

## 3. Treat state as a product contract

For every stateful workflow, define:

- durable state worth restoring;
- transient state that must not be restored;
- storage format and version migration;
- size/quota limits and what happens when they are reached;
- replacement cleanup and object URL/resource disposal;
- visible saved, restored, unavailable, and cleared states;
- an explicit clear/reset path.

Set `traits.stateful_user_workflow=true`; large media or uploads also set `large_binary_data=true`.

## 4. Test asynchronous state with durable signals

Fixed sleeps prove only that time passed. Expose a monotonic observable such as `data-saved-at`, revision, event id, or completed job id. Capture it before the action, wait for it to change, reload, and prove the same durable value is restored.

Use `captureAttribute`, `waitForAttributeChange`, `reload`, and `expectAttribute` in `browser_flow.mjs`.

## 5. Inspect the rendered product

- Capture desktop and mobile screenshots from a fresh artifact directory.
- Review hierarchy, wording, clipping, overlap, overflow, focus, and reduced motion.
- Use `expectNoHorizontalOverflow` and `expectNoOverlap` for known fragile regions.
- A screenshot is evidence only for the revision and run that produced it.

## 6. Separate release states

Use these exact states: implemented, locally verified, CI accepted, deployed, production accepted, externally pending, or blocked. A pushed commit or successful deployment is not production acceptance.

Verify a clean candidate revision, close the task with a source-equivalence manifest, deploy that revision, then execute production smoke and the real critical flow.

## 7. Keep verification non-mutating and artifacts owned

- Verification unexpectedly changing source files is a failed check.
- Declare an explicit reason only when mutation is intentional.
- Browser output directories must be fresh and contain `.harness-owned-files.json`.
- Never delete a broad evidence directory; only clean files declared by a harness ownership manifest.
- Run workspace hygiene before candidate creation and before handoff.

## 8. Design for real operating environments

- On Windows prefer `npm.cmd` when PowerShell script policy blocks `npm.ps1`.
- Treat `spawn EPERM` as a possible sandbox restriction; rerun the same bounded check with approved privileges before blaming product code.
- Remote media, fonts, providers, and demo assets require browser/network evidence plus a fallback or an explicit reliability decision.


## 9. Keep inference labeled until observed

- Repository conventions, framework defaults, and guessed URLs are useful hints, not executable truth.
- Mark discovery as `observed`, `declared`, or `inferred`; auto-enable only observed commands.
- A generated repo map may change without changing the product candidate fingerprint.

## 10. Persist only verified progress

- A worker report, plan update, or attempted edit is not durable progress.
- Across a session/model/context boundary, persist only milestones backed by fresh passing evidence.
- Keep rejected work and failed hypotheses as evidence so the next context does not repeat them as accepted state.

## 11. Skill presence is not Skill acceptance

- Shipping `SKILL.md` proves package topology, not autonomous discovery or value.
- Test both should-trigger and should-not-trigger cases; reject self-report as activation telemetry.
- For quality claims, prefer paired with-Skill / without-Skill evaluation and deterministic graders before model judges.

## 12. Make ceremony proportional to durability risk

- Use `native` when the current session can finish and verify honestly.
- Escalate to `portable` only when verified state must survive a boundary.
- Use `audited` for high-risk, security, release, or harness work.
- Execution profile changes persistence overhead; it never removes product-quality checks required by task traits.

## Definition of a complete product slice

A slice is complete only when the intended user loop works in the actual runtime, recovery and degraded behavior are known, claims match implementation, fresh evidence matches the candidate source, production behavior is accepted when release is in scope, and the workspace is clean enough for another engineer to resume safely.

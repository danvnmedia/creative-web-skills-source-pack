# Codex-First Product Playbook

## 1. Operating reality

This playbook assumes one Human Product Owner and one primary coding agent, normally Codex. Other models are optional fallbacks. Therefore:

- roles are review lenses, not fictional people;
- task contracts and evidence matter more than personas;
- deterministic tests/tooling replace as much subjective self-certification as possible;
- human attention is reserved for product/risk decisions, not routine implementation;
- repository artifacts carry memory across sessions and models.

The goal is the fastest trustworthy path from a real need to production behavior.

## 2. Seven invariants

1. **Useful before impressive.** A polished feature without a real user job is waste.
2. **Evidence before confidence.** A green statement is not a green check.
3. **Vertical slice before broad scaffolding.** Finish one useful loop end-to-end.
4. **Server/domain truth before client convenience.** Sensitive rules and entitlements are enforced authoritatively.
5. **Risk determines ceremony.** A CSS patch and an auth migration do not use the same process.
6. **Repository before conversation.** Durable decisions/state must survive model/session changes.
7. **Production behavior is the final truth.** Merge/deploy success is not user success.

## 3. Work classification

### PATCH
Use when desired behavior is already known and blast radius is small.

Path:
`inspect -> reproduce -> root cause -> minimal fix -> regression -> broader checks -> diff/adversarial review -> checkpoint`

Do not create heavyweight product documents.

### FEATURE
Use for a bounded capability with a clear user outcome.

Path:
`outcome -> acceptance -> UX/failure/security implications -> vertical slice -> verify -> checkpoint -> release if in scope`

### PRODUCT
Use for a new product, major workflow, unclear user need, or major redesign.

Path:
`reality/discovery -> define outcome -> risk-first MVP -> prototype/technical proof -> architecture/security -> vertical slices -> pilot -> production acceptance -> learn`

### CRITICAL
Use when failure has high consequence: auth, access control, sensitive data, children/student records, billing, destructive migrations, secrets, security infrastructure, regulated claims, major production operations.

CRITICAL adds stronger negative tests, recovery/rollback evidence, explicit Human Gates, and optional external review when actually available.

## 4. Compact lifecycle

### Stage 0 — Bootstrap / Reality Check

For a new repo:
- fill project charter;
- identify primary user/job;
- identify data/risk constraints;
- fill real commands;
- define quality baseline;
- create first task.

For an existing repo:
- inspect code, running behavior, routes, data model, auth, deployment and tests;
- do not assume docs are current;
- create a Product Audit if quality/state is uncertain.

Gate: the current problem or task is concrete enough to work on.

### Stage 1 — Discover the problem when needed

Do not run discovery for every bug. Run it when value/usability is uncertain.

Ask:
- who has the problem;
- what job are they trying to complete;
- what do they do now;
- where is the friction/cost/risk;
- how often does it happen;
- what evidence would disprove the idea.

Prefer behavior/history over hypothetical enthusiasm.

Gate: evidence is sufficient to justify the next investment.

### Stage 2 — Define the product outcome

Create only enough product definition to remove ambiguity:
- user and trigger;
- end-to-end value loop;
- non-goals;
- success metric/guardrails;
- main journey;
- failure states;
- acceptance criteria;
- relevant NFRs: security/privacy/performance/reliability/accessibility.

Gate: the agent can tell objectively whether the task is done.

### Stage 3 — Plan around risk, not files

Before implementation, map:
- affected UI/API/data/auth boundaries;
- source of truth;
- migration/dependency implications;
- external failure modes;
- observability needs;
- change budget/blast radius;
- exact verification ladder.

Use a spike when a technical assumption is high-risk and cheap to test.

Gate: major interfaces and risks are stable enough to build.

### Stage 4 — Build a vertical slice

A complete slice may include:
- data model/migration;
- domain rule;
- authorization;
- server/API action;
- UI;
- loading/empty/error/success states;
- analytics if useful;
- tests;
- docs/config.

Do not create 20 half-finished screens before one user can complete the core task.

### Stage 5 — Verify through evidence

Use the verification ladder, only where applicable:

1. deterministic schema/static/config checks;
2. unit/domain behavior;
3. integration/database/auth boundaries;
4. browser/mobile/keyboard/accessibility;
5. security negative tests;
6. performance/load/capacity checks;
7. production read-only/smoke checks after deployment.

For each important result, record what actually ran and what it proves.

### Stage 6 — Release safely

A release candidate must answer:
- which commit/SHA;
- required checks status;
- migration order;
- configuration/secrets readiness;
- rollback path;
- smoke/health/auth checks;
- monitoring after release.

Production acceptance requires proof that the intended deployed version behaves correctly in the real environment.

### Stage 7 — Operate and learn

Watch product and system behavior together:
- value-loop completion;
- activation/retention where relevant;
- error rate and latency;
- support/failed workflows;
- external provider failures;
- security/abuse signals;
- AI/provider quota and cost if applicable.

Use incidents and bugs to create regression guards and improve the environment, not just patch symptoms.

## 5. The Product Reality Gate

Before spending heavily on architecture or polish, the agent should be able to state:

```text
User:
Trigger:
Job/problem:
Current workaround:
Desired outcome:
Why current solution is insufficient:
Evidence we have:
Evidence we do not have:
Smallest useful value loop:
```

If the product is already in production, usage/support evidence may replace formal interviews.

## 6. Requirement quality

A requirement is ready when it contains:
- observable desired behavior;
- relevant error/permission states;
- explicit non-goals;
- data/auth implications;
- quality dimensions touched;
- acceptance checks.

Bad: `Make dashboard professional.`

Better: `On mobile 360px and desktop, a manager can identify the three overdue work items within one screen, open an item with keyboard or touch, and the dashboard remains usable while data is loading or partially unavailable.`

## 7. Risk-first MVP

The MVP is not the fewest screens. It is the smallest build that tests the biggest uncertainty.

Assess:
- value risk;
- usability risk;
- feasibility risk;
- viability/cost risk;
- safety/privacy/security risk;
- scale/reliability risk.

Build the slice that collapses the most dangerous uncertainty first.

## 8. UX as behavior, not decoration

UX review asks:
- Can a first-time user understand the next action?
- Is the main action visually and semantically clear?
- What happens while waiting?
- What happens when nothing exists?
- What happens when the user is not allowed?
- What happens on slow network or failed provider?
- Can the user recover/undo?
- Does mobile keyboard obscure controls?
- Does long text/translation break layout?
- Is feedback specific and truthful?

Do not postpone UX states until the “polish phase”.

## 9. Security by boundary

Do not treat security as a final checklist only. At each feature, identify:
- trust boundaries;
- authenticated actor;
- authorization object/action;
- tenant/ownership boundary;
- sensitive fields;
- attacker-controlled inputs/files/URLs;
- external providers and secrets;
- abuse/rate/cost surface.

Then create negative tests for the highest-impact boundary.

## 10. Scale and reliability by expected failure

Ask before claiming scale:
- expected normal and peak traffic;
- expensive endpoints/queries;
- list/file/job size limits;
- external dependency latency/failure behavior;
- timeout/retry/idempotency strategy;
- concurrency/race behavior;
- queue/backpressure/load-shedding needs;
- degradation path;
- load test evidence;
- capacity/headroom assumptions.

Do not optimize speculative bottlenecks, but do not leave work unbounded.

## 11. The single-model review pattern

Because Codex is normally both implementer and reviewer, use **separated review passes**, not fake personas.

### Implementation pass
Focus on meeting the task contract with minimal coherent changes.

### Verification pass
Run deterministic checks and reproduce behavior.

### Adversarial pass
Re-read acceptance criteria and final diff from the perspective of failure:
- how can permission be bypassed;
- where can stale/racing state appear;
- what happens on double-click/retry;
- where can data be lost or duplicated;
- what breaks on mobile/keyboard/long text;
- what query or call is unbounded;
- what provider failure cascades;
- what will operators see when this fails.

Label this honestly as self/adversarial review. If another model is available, it can perform the adversarial pass, but the process must not depend on that availability.

## 12. Human attention budget

The Human Product Owner should not approve routine engineering steps.

Agent decides:
- local implementation choices;
- normal refactoring inside task scope;
- test structure;
- small reversible UX choices consistent with existing patterns.

Human decides:
- what problem/user matters;
- material scope/pricing changes;
- sensitive data/privacy policy;
- destructive actions;
- meaningful cost commitments;
- major risk acceptance;
- production action when rollback/risk is unclear.

When escalation is necessary, present 2–3 options, recommendation, consequence, and the minimum decision required.

## 13. Brownfield product improvement

For an existing app, do not rewrite from scratch by default.

1. Audit actual behavior.
2. Create severity-ranked findings.
3. Identify the most important user-facing bottleneck or P0/P1 risk.
4. Fix one vertical slice.
5. Add a regression guard.
6. Re-run the relevant quality dimensions.
7. Repeat.

Prefer incremental architectural seams over “big bang” rewrites unless evidence shows replacement is safer/cheaper.

## 14. Session continuity

A session can disappear at any time. Therefore conversation is disposable.

At a meaningful checkpoint record:
- active objective;
- what changed;
- what passed;
- exact next command/action;
- open assumptions/blockers;
- branch/SHA.

Keep `.ai/RESUME.md` short enough that a fallback model can read it immediately.

## 15. Definition of Done

A task can be accepted when:
- the intended outcome exists end-to-end;
- applicable acceptance criteria have evidence;
- relevant error/permission states exist;
- no known release-blocking regression remains;
- final diff was reviewed adversarially;
- required docs/config/tests are updated;
- unverified claims are explicitly listed;
- state and resume checkpoint are current.

A product/release is stronger: it also needs production acceptance, monitoring, rollback readiness, and evidence for its scale/security claims.

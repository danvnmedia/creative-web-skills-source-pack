# Candidate, Closure, and Production Acceptance

Evidence is bound to a source fingerprint. Editing task metadata after verification used to make valid evidence stale. The closure manifest solves this without weakening source integrity.

## State machine

`working tree -> verified candidate -> closure metadata -> deployed exact revision -> production accepted`

These states must remain distinct in status reports.

## 1. Prepare the candidate

```bash
python .ai/scripts/workspace_hygiene.py --strict --allow-evidence
git status --short
```

Commit the product source and task contract. Do not include stale screenshots, caches, temporary files, or secrets.

## 2. Record fresh candidate evidence

```bash
python .ai/scripts/record_evidence.py --task TASK-123 --check build -- <build command>
python .ai/scripts/record_evidence.py --task TASK-123 --check runtime-browser -- node .ai/scripts/browser_smoke.mjs --url http://localhost:3000 --out .ai/evidence/browser/TASK-123-smoke --fresh-output
python .ai/scripts/record_evidence.py --task TASK-123 --check critical-flow -- node .ai/scripts/browser_flow.mjs --spec .ai/tasks/TASK-123-flow.json --out .ai/evidence/browser/TASK-123-flow --fresh-output
python .ai/scripts/evidence_gate.py --task TASK-123
```

`record_evidence.py` fails when the verification command unexpectedly changes the source fingerprint. Use `--allow-workspace-mutation-reason` only for an intentional, documented mutation.

## 3. Close without invalidating candidate evidence

```bash
python .ai/scripts/close_task.py --task TASK-123
python .ai/scripts/evidence_gate.py --task TASK-123
python .ai/scripts/completion_report.py --task TASK-123 --out .ai/evidence/completion-TASK-123.md
```

`close_task.py` records the candidate revision, candidate fingerprint, task-contract digest, allowed closure-only paths, required-check snapshot, waivers, and release identity. If product source changes afterward, the gate fails.

Commit only the closure metadata/evidence paths printed by the script.

## 4. Accept production

For `production_release=true`, the task must identify the production URL, deployed revision, CI evidence, rollback route, and revision marker. Record both:

- `production-smoke`: exact revision marker, availability, console/network health;
- `production-critical-flow`: the real user journey on production, including success and relevant degraded behavior.

Then accept the exact deployed closure revision:

```bash
python .ai/scripts/accept_release.py --task TASK-123 --production-url https://product.example --deployed-revision <SHA> --ci-url <CI-RUN-URL>
python .ai/scripts/evidence_gate.py --task TASK-123
```

Any final exact-revision observation after `accept_release.py` should be ephemeral so it cannot create an infinite commit-deploy-evidence loop:

```bash
python .ai/scripts/record_evidence.py --ephemeral --task TASK-123 --check post-closure-revision -- <exact revision probe>
```

Production acceptance remains `EXTERNALLY_PENDING` until the deployed revision and both production checks are observed.

## Invalid closure conditions

- candidate revision is not an ancestor of current HEAD;
- a non-closure source path changed;
- the task contract changed outside the recorded closure fields;
- required-check or waiver snapshots do not match;
- the production URL/revision/CI identity is absent for a release task;
- unexpected dirty source files exist.

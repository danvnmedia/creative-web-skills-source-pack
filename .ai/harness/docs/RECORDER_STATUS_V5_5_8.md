# Recorder process status - v5.5.8

Canonical compatibility/quality baseline: 5.3.0. Exact implementation parent:
5.5.7. This is a bounded correctness patch, not a new Skill or a redesign.

## Reproduced defect

The user's Codex report says a v5.5.6 security test passed 15/15, but its recorder
classified successful output mentioning DNS as external_dependency_failure.
That application result is user-reported, not independently rerun here.
Independent disposable CLI reproductions against the verified full 5.5.6 and
5.5.7 archives reproduce command_exit_code=0, exit_code=0, no source mutation,
status=blocked, and an evidence_gate exit of 1 for a successful DNS-labelled
fixture. The same class affects names of environment/security negative tests.

## Minimal correction

The recorder first checks the actual timeout signal. If the effective process
exit is zero, it returns process status pass without mining output for failure
words. Only a nonzero result is heuristically classified as environment,
security-boundary, external-dependency or product failure.

The caller still detects unexpected product-source mutation and rejects it.
The existing skill-eval-live contract still rejects self-report/generic commands.
Check/catalog identity, candidate and task freshness, mandatory check coverage,
output/log hashes, durable/ephemeral semantics and release revision checks are
unchanged. Explicit control-decision risk flags remain separate from output text.
No keywords were removed from the failure classifier and no retry was added.

Exit zero is a subprocess convention, not a universal assertion of product
correctness. A checker that detects a failed requirement must exit nonzero or be
validated by its dedicated structured contract. The recorder is not a semantic
validator for arbitrary stdout/JSON; printing PASS (or swallowing a failed child
exit) never supplies independent runtime, browser or live Skill evidence.

## Regression scope

`.ai/scripts/v558_regression_test.py` is auto-discovered by the existing mandatory
source regression gate and is registered as recorder-status-regression in the
check catalog. It tests success output with all existing keyword families,
nonzero failures, priority, timeouts, real subprocess capture, negative unittest
case names, missing executables, mutation, invalid live Skill evidence, missing
and stale checks, ephemeral evidence and preservation of prior failed events.
It can run in a source distribution or installed context; the full release
suite remains source-only. Its local subprocess fixtures are not an application
security suite, a live host activation eval or a production/browser acceptance.

## Upgrade and evidence preservation

Keep source outside the product repository. Use the new source installer:

```text
python INSTALL_HARNESS.py --target <product-root>
python INSTALL_HARNESS.py --target <product-root> --apply --confirm <plan-digest>
```

Use the same optional --repair-eol setting in both commands only when the
installer proves the scoped CRLF-to-prior-LF hash match. Do not normalize or
replace published artifact hashes. Existing v5.5.7 install preflight, exact-path
attributes, source/installed separation and explicit ownership repair remain.

Old events and completed tasks must not be edited or relabelled to pass. New
recorder behavior applies to new command executions. If a required check must
be rerun after a Harness/source change, do it for the current candidate (or a
successor task if already COMPLETE), with current hashes. A lifecycle-negative
runner can substitute only for a check explicitly covered by its trusted catalog
mapping, revision, execution context and environment. Similar descriptions or a
passing unrelated test are not interchangeable evidence.

INITIAL-LOAD-BUDGET is an application roadmap task and is out of this patch's
scope. Do not mix the Harness candidate with that application task's changes.

## Compatibility and cost

No dependencies or model/API calls are added. Successful commands skip heuristic
text scanning, but no end-to-end performance/token savings are claimed without
measurement. Native Windows/macOS and live IDE/Skill/production acceptance must
be reported separately from Linux subprocess regressions. Retain failure/skip
and partial-analysis states rather than treating them as PASS.

## Provenance

Local user/Codex field feedback received 2026-09-22; exact 5.5.6/5.5.7 reproductions
and a failing-before/fixed-after deterministic test are in the release evidence.
Python's primary subprocess reference documents the conventional meaning of a
zero returncode and the independent timeout condition:
https://docs.python.org/3/library/subprocess.html#subprocess.CompletedProcess.returncode
No external implementation, paid content or source catalog was vendored.

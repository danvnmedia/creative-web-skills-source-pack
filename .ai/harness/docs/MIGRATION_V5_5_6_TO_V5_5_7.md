# Migration v5.5.6 -> v5.5.7

Keep trusted source outside the product workspace. Review preflight CI references,
state portability and every path before the transactional apply.

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT"
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT" --apply --confirm PLAN_DIGEST
```

Default still blocks drift. For a proven CRLF-only ownership transform, review an
explicit repair plan and retain the same flag in the apply call:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT" --repair-eol
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT" --repair-eol --apply --confirm REPAIR_PLAN_DIGEST
```

Repair compares CRLF->LF diagnostic bytes with the prior raw hash, then restores
trusted source bytes. No hash normalization/adoption, BOM removal or mixed-edit
repair. Keep a separate snapshot; successful install transactions remove raw backups.

## Git/CI

The managed comment block in `.gitattributes` lists exact owned files and mixed
managed-block containers, never all product files. `-text -filter -ident
-working-tree-encoding` preserves raw bytes through checkout. Existing outside-block
bytes are preserved. Review entries that overlap intentional custom filters.
No mass working-tree normalization or global Git setting changes.

Commit reviewed `.ai/HARNESS_INSTALL_STATE.json`, `.gitattributes` and intended
managed paths for reproducible installed CI. Do not stage old tasks, checkpoints,
logs or unrelated dirty evidence. Tracked and ignored are diagnosed separately.
Preserve the managed .ai/checkpoints/README.md and .ai/evidence/README.md in Git;
ignore their runtime siblings, not the whole directory. Nested .gitattributes or
.git/info/attributes may override root rules; installed verification remains required.

```powershell
python .ai/scripts/verify_installation.py --root .
python .ai/scripts/self_test.py --context installed
python .ai/scripts/surface_drift.py
```

Source validation, package_release, `verify_package --path .` and full regressions
belong in the trusted source tree, with scratch outside source. Explicit
`verify_package --path <trusted-zip>` remains a valid archive check. Reference scan
is bounded/lexical, not proof it found every dynamic shell/CI invocation. Legacy
prose is not auto-deleted; three compatibility doc paths remain for canonical Skills.

## Release

1. Prepare intended runtime URL, rollback and marker contract before tests.
2. Commit product/task changes, record fresh evidence, then close_task.
3. Commit closure-allowed paths only; deploy that exact closure revision.
4. Record durable production-smoke and production-critical-flow on that deployment.
   Evidence can remain uncommitted for acceptance; do not redeploy just for receipts.
5. accept_release verifies the exact revision/URL/CI reference.

`record_evidence --ephemeral` is supplemental and cannot satisfy required production
checks. Observe the deployed FULL 40/64-character commit marker; short prefixes are rejected.
Do not just echo an expected SHA. COMPLETE is
terminal; use a new task for a new candidate. Actual URL/revision/artifact changes
still invalidate evidence. Only closure receipt creation was removed from runtime
identity. Existing events are never relabeled after this Harness upgrade.

## Windows/local server

Prefer separated argv for complex paths:

```powershell
python .ai/scripts/with_server.py --server-argv '["npm","run","dev"]' --port 3100 --identity-path /build-info.json --identity-key revision --identity-value OBSERVED_EXPECTED_REVISION -- python test_flow.py
```

Example only: the app must serve the observed endpoint/key and port. Occupied port
is refused before verification; no silent fallback. Without identity arguments only
port readiness is known. Batch metacharacters require an approved direct native/Node
entry point; .ps1 is not automatically given an execution-policy bypass. Native
Windows tests must run natively, not be inferred from Linux mocks.

## Task/UX

validate_task lists valid modes, custom-check warnings and advisory Skill preparation.
This is not telemetry or new permissions. Filled FEATURE/RELEASE and UX examples
live in `.ai/harness/templates` after install. Optional `.ai/UX_TOKENS.json` is
project-owned and source-fingerprinted; structural validity does not prove visual
quality or accessibility. No UI Skill behavior changed in this release.

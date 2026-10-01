# v5.5.7 field triage - reported experience vs reproduced mechanisms

Input: user-supplied Claude report after 10 product tasks, received 2026-09-22.
It is field evidence, not independently audited access to the user's production,
CI or installed files. This release was built in an isolated copy of exact v5.5.6.
It never edits the user's application or treats every suggested fix as safe.

| Item | Finding and disposition |
|---|---|
| 1 Legacy agent prose | Confirmed preservation mechanism. New read-only preflight identifies known legacy hashes / unknown outside-block text. Automatic cleanup is NOT implemented: unknown text stays intact, known matches are archive-review candidates, not deletion authority. |
| 2 Three duplicated doc paths | Intentional compatibility pointer containers for unchanged canonical Skills. New installs already use pointers. Existing outside-block legacy prose may remain; diagnose it, never drop paths Skills still reference. Full legacy retirement is deferred pending proven ownership and reviewed migration. |
| 3 CI references | Bounded `.github/`, root build file and docs scan in plan/digest; recommendations distinguish source-only, explicit-source-path and valid context-sensitive commands. Lexical, not a YAML/shell interpreter. No auto rewrite/execution. |
| 4 Ignored state | Doctor/preflight checks tracked vs ignored state. Commit reviewed `.ai/HARNESS_INSTALL_STATE.json` for installed-context CI; checkpoints/logs remain runtime artifacts. Git failure is unknown, not tracked/healthy. |
| 5 CRLF hashes | Do NOT normalize ownership/archive hashes. Exact-path Git attributes preserve bytes and disable text/filter/ident/encoding transformations on named owned files/managed containers. Explicit `--repair-eol` plans may restore only CRLF changes whose normalized bytes match the prior raw LF hash; other drift/BOM/content changes remain conflicts. |
| 6 Release order | close_task points to release-acceptance and closure commit -> exact deployment -> durable production evidence -> acceptance. `--ephemeral` is supplemental; it cannot satisfy mandatory production checks because it stores no event. |
| 7 Runtime digest | Reproduced more precise cause: adding closure receipt fields changed runtime digest even with identical task/product bytes. close_task URL flag writes the receipt, not task.release. Removed only closure receipt fields. Actual task URL/revision/marker/artifact/deployment IDs remain bound; environment changes invalidate evidence. |
| 8 Complete task | Immutable closure and terminal tasks retained. Error directs a new successor task for a new candidate. No new SUPERSEDED state or overwriting old evidence. |
| 9 Errors | Missing closure prints expected path/state. Revision error explains observed marker/output_tail, not echoing an expected SHA as a fake probe. URL mismatch rejected. |
| 10 Windows npm | Existing --server already used shell=True; report alone does not identify which subprocess failed. Conservative resolver shared by recorder and server/verification paths, explicit system cmd host for safe .cmd/.bat arguments. Ambiguous metacharacters refused; .ps1 needs explicit host, no policy bypass. Linux run is not native Windows acceptance. |
| 11 Wrong server | Existing helper had required --port, not hidden 3000 default. Actual gap: occupied port could look ready. It refuses an existing listener before launch/check and optionally verifies bounded in-origin JSON identity. Port-only mode states identity NOT_VERIFIED. No silent auto port switch. |
| 12 Mode enum | Schema authority for FEATURE/BUGFIX/AUDIT/CRITICAL/RELEASE/MAINTENANCE. Contradictory PATCH/PRODUCT prose corrected; validation lists values, no silent coercion. |
| 13 Custom checks | Unknown IDs get warnings; still require evidence, never alias/replace canonical checks. Built-in trait checks may use observed project runners. |
| 14 Examples | Filled FEATURE/RELEASE examples, namespaced on install. READY, no fabricated evidence; replace fictional assumptions/URL before executing. |
| 15 Trait-to-Skill | Machine-readable advisory map and hints. No automatic load claimed; selection/presence is NOT activation. Live acceptance unchanged. |
| 16 UX | Optional project `.ai/UX_TOKENS.json` schema/structural validator/example. No invented real design system installed. Declared tokens are not visual/usability/a11y acceptance. No canonical Skill changed. |

## Sources/license

Original implementation based on a user-authorized field report and existing
Harness contracts. No third-party implementation copied or vendored.
Primary references checked 2026-09-22:
- https://git-scm.com/docs/gitattributes
- https://git-scm.com/docs/git-check-ignore
- https://docs.python.org/3/library/subprocess.html

No fixture output proves that the user's production volume defect, host activation,
UI or deployment is now accepted.

## Additional defect reproduced during this review

The original v5.5.6 revision comparator accepted an empty actual revision, short
prefixes and overlong strings beginning with the expected SHA. It now requires
equality of complete 40/64-character hexadecimal commit IDs. Production smoke must
contain the complete observed marker token, not only seven characters. This is a
deterministic closure-identity hardening, not evidence that any real deployment
was exploited or reaccepted. CLI errors and negative cases cover this boundary.

The first full candidate run passed all 17 regression runners but failed source
package identity checks because current verifier constants/README still referred
to 5.5.6. Current bindings were corrected; historical lineage assertions remain.
The source package verifier now also runs BEFORE the expensive regression suite.
Failed/partial attempts remain evidence and are never counted as release PASS.

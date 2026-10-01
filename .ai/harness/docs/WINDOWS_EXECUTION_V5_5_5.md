# v5.5.5 - Windows Execution Boundary Lessons

Canonical compatibility/quality baseline: 5.3.0. Implementation parent: exact 5.5.4,
SHA-256 fdbaf29e365d0bafc3d3e56e4dca0fc3c50babf449c7726873cdcbf4fc17553c.
The 13 canonical Skill bodies remain byte-identical. This patch is a v5.3.x-sized
correctness/reliability change, distributed as 5.5.5 on the existing lineage.

## Incident and independent reproduction

The user reported a native Windows upgrade from 5.4.5 to 5.5.4: installed checks
passed, full source suite initially failed, WSL later passed 14 runners. The
reported CI and deployment URLs are user-supplied evidence. Connector fetch of
the Quality run returned 404 in this session; no CI/deployment claim was
independently verified. Nothing was pushed, installed in the real product,
removed from the user's project, or deployed by this maintenance run.

Four exact defects reproduced locally against the unmodified parent:
1. The full regression runner read product-root VERSION after an installed run.
2. Copy tests could choose a temp destination under the source being copied.
3. Git stderr diagnostics shared the stream parsed as paths.
4. Skill frontmatter parsed LF only; valid CRLF falsely appeared to lack metadata.

The fourth is a production parser defect, not merely a disposable fixture issue.
No global core.autocrlf change, warning suppression, scanner-disable, skipped
failure or newline rewrite of canonical Skills is the fix.

## Implemented

- Source-only full-suite runner refuses installed context before invoking tests;
  list-only uses the existing namespaced harness_version resolver. Installed
  self_test.py remains the correct installed integrity/security route.
- Copy-safe temp selection excludes the source (including resolved aliases),
  before a writable probe; copy_source_tree separately rejects overlapping trees.
  --temp-root is available on the full runner and release packager. Child-only
  TMPDIR/TEMP/TMP/HARNESS_TEMP_DIR/HARNESS_TMP agree; the parent's environment and
  global Git settings are unchanged. Generic non-copy runtime temp remains valid.
- The bounded existing evidence runner is reused for per-regression timeout and
  output capture, rather than adding a second subprocess framework. Its reader
  now explicitly closes the output pipe at EOF/error; a regression rejects the
  prior ResourceWarning instead of suppressing warnings.
- Git stdout and stderr are separate. File lists use NUL; status uses porcelain
  v1 -z and includes both rename paths. Paths are not stripped/quote-guessed.
  Git errors fail instead of producing an empty supposedly-clean fingerprint.
- Frontmatter structure tolerates CRLF and one leading UTF-8 BOM in memory only;
  separators must occupy their own lines. Missing/ambiguous metadata remains a
  review finding. Byte hashing/install/repair/manifest semantics are unchanged.
- Runner reports source/installed context, actual OS/kernel/Python, observed Git
  version/config, per-script output digest and explicit unittest SKIP counts.
- Packaging checks source bytes before/after tests and refuses mutation rather
  than rebuilding a manifest to conceal it.

## Practical commands (Windows / PowerShell examples)

Keep the extracted source OUTSIDE the product project. For an isolated sibling
scratch location outside that source directory:

    python .ai/scripts/deterministic_regression_gate.py --temp-root "D:/HarnessScratch" --out "D:/HarnessScratch/regression.json"

In the installed product directory:

    python .ai/scripts/self_test.py --context installed

From the extracted source directory, plan the upgrade first:

    python INSTALL_HARNESS.py --target "D:/Projects/YOUR_PROJECT"
    python INSTALL_HARNESS.py --target "D:/Projects/YOUR_PROJECT" --apply --confirm PLAN_DIGEST

A supported shell path is not authorization to create a global config, enable
permissions, install tools or run paid/live services. The commands above require
an actually writable authorized location. An unavailable temp base is BLOCKED,
not permission to broaden the sandbox.

## Test fixture environment isolation

The first full-suite attempt for this patch correctly failed v550's legacy temp
override fixture: it set HARNESS_TMP but inherited higher-priority HARNESS_TEMP_DIR.
The fixture now clears the conflicting selector in its child-only environment.
Production precedence is unchanged. Two new tests pin both precedence and the
legacy override. The failed attempt stays in external release evidence.
Final preflight also corrected the implementation-parent metadata to exact 5.5.4;
a dedicated regression now pins the lineage and input-artifact SHA-256.
A later log review reproduced an unclosed pipe in the parent capture helper.
The unreleased intermediate candidate and its warning logs remain development
evidence, not final acceptance. The final suite reruns after a reader-owned close.

## Evidence and cleanup lessons not overstated as new functionality

Keep an evidence matrix, not one ambiguous PASS: exact source on Linux, source on
WSL, source native Windows, installed native Windows, product CI, deployment
revision and production user-flow acceptance are distinct claims. WSL PASS may
corroborate Linux source behavior; it cannot erase the preceding Windows FAIL.
CI success/deployment success do not establish production UX acceptance.

A shared catalog runner may satisfy only the checks that its pinned catalog maps
and that its actual invocation/context/OS/revision covers. Do not multiply 14
runner invocations into dozens of independent reviews or silently import WSL
results as native-Windows evidence. Existing task evidence remains task-scoped.

Do not keep release source inside product root merely because it is gitignored:
Git ignore alone says nothing about deployment/upload/indexing. Prefer an
external, versioned source cache. Moving a formerly tracked old release is a
separate product change with its own exact diff; never delete by wildcard.
Deletion requires current path/ownership/reparse checks, explicit scope and
verified replacement. This release does not add or invoke an auto-delete tool.

## Acceptance limits

This maintenance environment is Linux, not native Windows/WSL. CRLF, BOM, Git
warning and path-alias regressions are deterministic fixtures, not an OS emulator.
Native Windows retest (restricted temp, junctions, long/Unicode paths and exact
5.5.4 migration), live hosts, autonomous Skill activation, causal lift and product
production acceptance remain unclaimed unless separate fresh evidence exists.
No tests or trait-derived quality requirements have been removed.

## Public references; no upstream implementation copied

- Git porcelain/NUL contract: https://git-scm.com/docs/git-status
- Python temporary-directory resolution/caching: https://docs.python.org/3.13/library/tempfile.html
- Public Vietnamese-builder CLI reviewed: https://github.com/mrgoonie/claudekit-cli
- Newly surfaced China-origin adjacent runtime reviewed: https://github.com/howtimeschange/crawshrimp-harness
- Low-activity multi-agent preset reviewed but not adopted: https://github.com/bernardleex526/oh_my_deepseek_harness

The concrete patch is independently derived from the user's incident and exact
local reproduction, not from unverified upstream marketing or paid kit content.
External repo discovery did not justify adding a multi-agent/runtime dependency.

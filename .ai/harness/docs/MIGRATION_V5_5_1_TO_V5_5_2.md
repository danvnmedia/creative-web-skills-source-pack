# Migration 5.5.1 -> 5.5.2 (canonical baseline 5.3.0)

Keep the source ZIP/extracted package OUTSIDE the product repository. Do not copy
README.md, VERSION, docs/, AGENTS.md or the whole archive content over project files.
The existing collision-aware installer plans namespaced payload and managed blocks.

From the extracted source directory, first run:

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT"
```

Review the returned plan, conflicts, prior version and exact plan_digest. Apply only
that reviewed current digest (do not type the placeholder literally):

```powershell
python INSTALL_HARNESS.py --target "D:\Projects\YOUR_PROJECT" --apply --confirm DIGEST_FROM_PLAN
```

Project-owned content outside managed blocks, edited task/state, checkpoints and
existing evidence are preserved. A local managed-payload edit becomes a conflict,
not permission to overwrite it. The old workflow is not silently rewritten. Unknown,
newer, or detected foreign skill-first topology is blocked for a separate staged
migration; do not bypass this by deleting ownership markers. The inherited installer rolls back a failed apply automatically; after a successful
apply it removes raw transaction backups. Before upgrading, keep an external project
snapshot or source-control checkpoint for any later operator-led rollback. Do not
restore an old whole-project snapshot over newer task/evidence state. Validate the
installed copy with verify_installation.py and self_test.py.

Important evidence transition: historical activation rows remain readable with
--legacy-diagnostic but no longer satisfy skill-eval-live. No evidence is deleted.
Affected tasks must collect strict live evidence or retain an explicit unexpired
human-approved waiver. An unsupported host does not weaken the gate. Existing
product checks, candidate closure and production-revision acceptance are unchanged.

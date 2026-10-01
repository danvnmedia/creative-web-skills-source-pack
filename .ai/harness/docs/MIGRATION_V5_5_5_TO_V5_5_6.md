# Migration: v5.5.5 -> v5.5.6

Canonical baseline remains 5.3.0. Additive parent is exact v5.5.5, not the unrelated
older skill-first 5.6 branch. All 13 canonical SKILL.md bytes are unchanged.

1. Keep the release source outside the product repository. Verify ZIP checksum and
   manifest. The normal installer is plan-first; review its exact digest/conflicts.
2. Run `python INSTALL_HARNESS.py --target PATH`, then apply that exact reviewed plan
   with `--apply --confirm DIGEST`. Do not manually merge root metadata/docs.
3. Use installed self-test in the product repository, full release regression in the
   separate source workspace. Keep scratch outside source; Windows is not Linux/WSL.
4. Existing task files need no new required field and no automatic migration. Add
   optional prompt_context only when useful; changes invalidate task-bound evidence.
5. Brief generation is on-demand. Existing implementation workflows still execute;
   no new 14th Skill or globally installed prompt plugin is added.
6. Existing project context/README/AGENTS text outside owned blocks remains preserved.
   Installed documents remain under `.ai/harness/docs/`; scripts remain `.ai/scripts/`.
7. `prompt-brief-contract` is added only for Harness modifications. No old trait gate,
   live Skill requirement, execution profile requirement or browser gate is removed.
8. Explicit --save uses excluded-but-validated checkpoint runtime storage. To use a
   stale capsule, regenerate after canonical task/source/evidence verification.

New metadata/scripts: PROMPT_BRIEF_POLICY.json, prompt_context.schema.json,
prompt_brief.py, v556_regression_test.py and .agents/workflows/brief-task.md.
Existing task schema, digest projection and runtime validator receive bounded hooks.
No global model selection, host permission or active product deployment changes.

Rollback during failed install follows the existing transaction mechanism. A
successful install is not a permanent undo backup: preserve an independent project
snapshot before applying. Do not automatically downgrade newer installed versions.

Historical v5.5.5 release-lineage assertions read the byte-identical archived
`.ai/lineage/v5.5.5.json`; the new regression separately checks current v5.5.6
identity, exact v5.5.5 parent hash and archive hash. No historical behavioral
assertion is deleted and no published v5.5.5 archive byte is modified.

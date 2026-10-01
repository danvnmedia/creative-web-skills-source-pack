# Harness v5.5.10: installation record

- Target: `D:\Projects\SKILLS\creative-web-skills-source-pack` at baseline `a994649` on rollback branch `codex/harness-skills-motion-20260930`.
- Source: sibling distribution `D:\Projects\IMAGES\black-florest-app-clear-main\Codex_Product_Harness_v5.5.10`; version `5.5.10`.
- Read-only plan: 273 changes (265 creates, 8 safe merges), no conflicts, digest `c3a9447cc96f35ffb1149ef45ec42d4397088cf1f398194cc0e8f2b76c19aeb5`.
- First apply failed with `WinError 5` while replacing `.gitattributes` in the restricted execution context. The installer retained a transaction record and left the plan unchanged. Retrying the exact digest with workspace write access passed.

## Commands run

```powershell
git switch -c codex/harness-skills-motion-20260930
python INSTALL_HARNESS.py --target D:\Projects\SKILLS\creative-web-skills-source-pack
python INSTALL_HARNESS.py --target D:\Projects\SKILLS\creative-web-skills-source-pack --apply --confirm c3a9447cc96f35ffb1149ef45ec42d4397088cf1f398194cc0e8f2b76c19aeb5
python .ai/scripts/bootstrap_project.py --write
python .ai/scripts/harness_doctor.py
python .ai/scripts/self_test.py --context installed
python .ai/scripts/verify_installation.py --root .
python .ai/scripts/skill_eval.py validate
python .ai/scripts/surface_drift.py
python .ai/scripts/harness.py verify --profile native
```

## Result and limits

Installed self-test, ownership verification, drift check, static Skill routing contract (26 cases across 13 canonical skills), and native verify-all pass. Doctor reports no root project command because the runnable Asme package is nested; the repository command map will be completed during the audit/upgrade. Installer advises committing `.ai/HARNESS_INSTALL_STATE.json` so a fresh checkout retains ownership provenance. Static Skill checks do not prove live autonomous activation. No production deployment is implied.

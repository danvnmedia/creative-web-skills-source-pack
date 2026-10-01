# Completion Gate

The completion gate converts quality promises into a machine-checkable minimum.

Task traits automatically add required checks from `.ai/QUALITY.json`. Example:
- `user_facing_web` → `build`, `runtime-browser`;
- `ai_integration` → `ai-contract`;
- `security_sensitive` → `security-negative`;
- `performance_sensitive` → `performance`;
- `production_release` → `production-smoke`.

Each check must have a latest `pass` event for the current workspace fingerprint.

Human-approved waivers are explicit task records; silent omission is not a waiver.

Run:

```bash
python .ai/scripts/evidence_gate.py --task TASK-123
```

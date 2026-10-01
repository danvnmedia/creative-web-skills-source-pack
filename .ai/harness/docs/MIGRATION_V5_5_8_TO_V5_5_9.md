# Migration v5.5.8 -> v5.5.9

v5.5.9 is a small Harness control-plane update. It does not modify the 13 canonical Skills.

- `release_doctor.py` is read-only: it does not fetch, push, deploy, promote, rewrite refs, or mutate tasks. Provider CI/deployment/alias state stays `UNKNOWN` unless independently supplied/verified elsewhere.
- `validate_task.py` warns early when a production-release task lacks an observable revision marker. The warning is not production acceptance.
- `record_evidence.py --summary` changes only terminal rendering; default JSON and persisted evidence remain unchanged.
- `AI_PROVIDER_POLICY.json` moves to v2. Authorized failover across eligible independent capacity is explicitly machine-readable; paid fallback still requires project authorization/budget, same-scope keys are not new capacity, and provider restrictions/spend caps remain fail-closed.
- Legacy project policy v1 remains accepted by `provider_policy_lint.py` during migration. New source distributions ship v2.

No API calls, billing activation, deployment, or active project changes are performed by this migration.

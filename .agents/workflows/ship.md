# Ship
1. Load `release-acceptance`.
2. Confirm the task resolves to `audited` and has fresh `verified-progress`.
3. Run the active task evidence gate.
4. Confirm candidate revision and migration/rollback readiness.
5. Deploy through approved path.
6. Confirm deployed revision.
7. Run real production/staging smoke and the production critical flow.
8. Record `production-smoke` and `production-critical-flow`; distinguish deployed from production accepted.
9. Run `accept_release.py` only for the exact deployed candidate.

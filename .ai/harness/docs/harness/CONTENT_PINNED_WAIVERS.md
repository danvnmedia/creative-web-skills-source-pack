# Content-pinned waivers

A waiver is not a boolean bypass. It accepts one concrete, current finding for a bounded time.

Required waiver fields are `check`, `reason`, `owner`, `approved_at`, `expires_at`, `finding_id`, `accepted_finding_sha256`, `accepted_scope`, and `human_approved=true`. The referenced finding lives in `verification.findings[]` and includes the check, severity, component, attack path, and evidence references.

`.ai/scripts/_common.py` recomputes the finding digest and scope on every gate. A changed severity, component, attack path, evidence reference set, expired timestamp, missing owner/reason, or digest mismatch invalidates the waiver. `close_task.py` snapshots both the waiver digest and referenced finding; `evidence_gate.py` revalidates expiry and digest after closure.

This is intentionally fail-closed. Older task files with boolean-only waivers must be migrated rather than silently grandfathered.

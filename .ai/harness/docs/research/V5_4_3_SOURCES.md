# v5.4.3 Public Mechanism Notes

Canonical comparison baseline: Codex Product Harness v5.3.0. Only public mechanisms were studied; implementation here is local and purpose-built.

## sdsrss/agentsmd — checked 2026-09-12

Fresh public repository with active work and MIT license. Relevant public mechanisms: sentinel-managed blocks that preserve content outside them; manifest-backed ownership; staged changes; snapshot checks; compare-and-swap before writes; plan/repair digests that become stale when target bytes change; rollback; refusal of symlinked shared logical paths; separation of plugin/standalone runtime state.

Gap addressed: v5.3/v5.4.2 ownership-aware install protected obvious conflicts but did not model installation as a reviewed transaction and did not cleanly separate release-source validation from runtime installation inside an application repository.

Local adaptation: `.ai/INSTALL_POLICY.json`, `.ai/scripts/install_plan.py`, install state schema 2, marker-scoped agent/doc pointers, plan-digest CAS, transaction rollback, and explicit source-vs-installed validators. No external dependency and no code copied.

Expected impact: zero model-token overhead; one deterministic hash/plan pass before install and small file-hash checks during apply.

Release level: v5.4.3 safety/operability hardening, not v6.

## SUNRNEHUI/agent-harness — checked 2026-09-12

The public v10.0.0 documentation continues to reinforce keeping the runtime package boundary explicit and excluding repository-only material from the runtime bundle. This supports the source-vs-installed separation but does not require importing its orchestration model.

## Rejected complexity

No new multi-agent orchestration, memory subsystem, or duplicate Skill catalog was added. The observed failure is a packaging/ownership boundary error and is better solved by deterministic filesystem contracts and regressions.

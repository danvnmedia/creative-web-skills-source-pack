# Migration: v5.4.1 to v5.4.2

1. Install/repair through the ownership-aware installer; do not overwrite user-owned conflicts silently.
2. Existing tasks without waivers continue unchanged. Existing boolean-only waivers are intentionally invalid and must be converted to content-pinned, expiring waivers with a current `verification.findings[]` entry.
3. Failed verification loops may record `--hypothesis-id`; use `control_decision.py` instead of blind retry when deciding ACCEPT/RETRY/REPLAN/ROLLBACK.
4. For tasks that actually use MCP, set `traits.mcp_runtime=true`, pin the trusted host-enumerated surface, and record fresh `mcp-surface-pin` evidence. Do not set this trait merely because an MCP config file exists.
5. Runtime decision and MCP pin files under `.ai/checkpoints/**` remain excluded from candidate fingerprint/source dirt and release payloads.
6. The 13 canonical Skills are byte-identical to the v5.3.0 baseline; no Skill eval waiver is needed for this harness-only release.

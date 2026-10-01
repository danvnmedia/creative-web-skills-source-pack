# Verified checkpoints

Runtime-generated checkpoint files live here and are not part of the release ownership manifest.

Only evidence-backed, verified progress may be persisted. Do not store hidden reasoning, full chats, secrets, provider session objects, or unverified worker claims.

Runtime subtrees used by v5.4.2:
- `decisions/`: deterministic ACCEPT/RETRY/REPLAN/ROLLBACK records.
- `mcp/`: approved MCP tool-surface pins.
These remain runtime state: validated when used, excluded from candidate fingerprint/source dirt and packaged release payload.

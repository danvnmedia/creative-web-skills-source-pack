# MCP surface pinning

The harness does not start an MCP server to decide whether that server is safe. A trusted host/adapter enumerates the current tool surface to JSON, then `.ai/scripts/mcp_surface_pin.py` pins it.

The pin binds server identity plus each tool's name, description hash, input-schema hash, and capability class. Reconnect/resume verification returns `review_required` for a changed server identity, added/removed tool, changed description, changed input schema, or changed capability class. Reordering JSON or tool entries does not create drift.

Pins live under `.ai/checkpoints/mcp/**`, so they remain validated runtime state while staying outside candidate fingerprints and release payloads. For MCP-backed tasks set `traits.mcp_runtime=true`; the quality policy then requires `mcp-surface-pin` evidence.

`guard-call` provides a small deterministic pre-tool boundary: the tool must exist in the pin, sensitive argument keys require explicit allow, and absolute path arguments may not escape the project root by default. It never executes the MCP server itself.

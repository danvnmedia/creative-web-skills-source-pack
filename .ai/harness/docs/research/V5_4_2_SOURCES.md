# v5.4.2 mechanism provenance

This release reimplements small public mechanisms; it does not vendor external repository code or paid/proprietary content.

- BOUND (`Danny-de-bree/bound`, MIT): inspiration for deterministic controller outcomes instead of free-form retry. Local implementation is reduced to single-primary-agent evidence/budget/checkpoint decisions.
- Attestral (`attestral-labs/attestral`, Apache-2.0): inspiration for content-hashed, expiring risk acceptance. Local implementation pins a waiver to the exact current finding digest and scope.
- MCP-Scan lineage (`mansilladev/mcp-scan`, Apache-2.0 in the reviewed public repository lineage): inspiration for detecting MCP tool-surface drift/rug-pull behavior. Local implementation consumes trusted host enumeration JSON and never executes an MCP server during pin/verify.

Canonical product/harness baseline remains Codex Product Harness v5.3.0. All v5.1-v5.3 mechanisms remain regression-protected; v5.4.1 controls remain additive.

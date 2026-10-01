# Skill / Plugin / MCP Quarantine

Treat newly imported Agent Skills, plugin archives, and MCP configuration as untrusted input before install or activation. `quarantine_scan.py` is deterministic and local: it inspects archive topology and text patterns, enforces size bounds, rejects traversal/symlink escape and secret-like material, and never executes scanned MCP commands.

`block` means do not install. `review` means capability deserves human/security review; it is not a safety certificate. Cache results only by content SHA so any byte change invalidates the prior result. External scanners may add evidence, but the harness does not make them a mandatory runtime dependency.

## v5.5.4 executable-content coverage

The deterministic quarantine scanner also performs bounded Python AST sink analysis and explicit opaque-executable coverage. A recognized compiled/executable payload that the text/AST analyzers cannot inspect makes `analysis_status=partial`; it is not a clean scan. Statically reconstructable reflective Python `exec`/`eval` is blocking. Target code is never executed to improve coverage.

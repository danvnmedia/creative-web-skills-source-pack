# Harness Security

The coding harness is itself an attack surface. Its instructions, scripts, Skills, config, adapters, and install lifecycle can change what an agent is allowed to do.

`harness_security.py` performs a deterministic baseline scan of harness-owned surfaces for:

- secret-like credentials and private keys;
- environment files that should not ship;
- Unicode bidi control characters;
- escaping or broken symlinks;
- pipe-to-shell install patterns;
- obvious root-destructive shell patterns;
- world-writable files/commands.

This is a baseline, not a substitute for project-specific security review. New executable hooks, remote installers, MCP servers, permission changes, or supply-chain dependencies require focused human/security review even when the static scan passes.

For a harness-modification task, record `harness_security.py` as `harness-security` evidence.

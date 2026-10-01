# Cross-platform reliability

v5.5 makes Windows a first-class regression surface:

- exact-file regression restore is raw bytes, preserving CRLF/encoding;
- temporary work uses `HARNESS_TMP`/explicit writable roots, probes the OS temp directory, then falls back to `.ai/checkpoints/tmp/`;
- temp directories carry a Harness lease marker and failed cleanup records an exact residue path;
- `harness.py cleanup` only deletes paths with a Harness lease marker;
- POSIX world-writable checks use mode bits only on POSIX; Windows uses `icacls` and distinguishes explicit broad-write ACEs from inherited permissions;
- browser doctor output distinguishes project-local reproducible Playwright from Harness scripts, host browser capability and borrowed logged-in browser leases.

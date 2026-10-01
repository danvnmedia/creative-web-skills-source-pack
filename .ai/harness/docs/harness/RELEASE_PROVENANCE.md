# Release Provenance and Exact Artifact Acceptance

The distributable identity is the exact verified ZIP, not the working tree or filename. v5.4.1 produces:

- `.ai/HARNESS_MANIFEST.json` for managed source ownership;
- `SBOM.spdx.json` using SPDX-2.3 with per-file SHA-256;
- a sidecar release witness binding exact ZIP hash/size/file count plus embedded manifest and SBOM hashes;
- optional Ed25519 signing.

An embedded public key can prove that a signature matches the embedded key, but cannot by itself establish who owns that key. `release_witness.py verify` reports `verified-untrusted-key` unless the verifier supplies an out-of-band trusted public key; only then is signer identity reported as proven.

`package_release.py` verifies the source, writes the ZIP, verifies the exact ZIP, re-extracts it, verifies the extracted bytes again, then creates/verifies the witness. Loader/export changes also require causal/runtime evaluation against the exported artifact rather than source-only success.

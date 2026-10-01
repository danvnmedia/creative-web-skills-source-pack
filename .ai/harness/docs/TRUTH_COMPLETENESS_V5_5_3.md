# v5.5.3 Truth and completeness controls

## Security completeness

A scanner returning no finding is useful only when the required analysis actually completed. `harness_security.py` now records requested/completed analyzers and incomplete reasons. `skill_security_gate.py` records `analysis_status`, resource-limit hits, and treats incomplete ingest/text analysis as blocking even when the associated finding fingerprint appears in an explicit baseline.

This remains deterministic static analysis. It does not claim semantic, dynamic, or runtime immunity.

## Deterministic regression discovery

`deterministic_regression_gate.py` discovers every `*_regression_test.py`, records the SHA-256 of each test plus the Python executable used, and executes all discovered deterministic regressions. `--list-only` produces `NOT_RUN`, never PASS. Live/model/external E2E is intentionally a separate evidence class.

## Skill catalog routing

`.ai/evals/skill-catalog-routing.json` exposes the full 13-Skill catalog for positive/negative cases and excludes the target for a separate baseline. `skill_catalog_eval.py validate` checks matrix integrity. Scoring accepts only configured activation sensors; self-report, generic reads, prose, forced slash commands, fixtures, and unbound labels remain non-proof.

## Host surface drift

`host_surface_contract.py` accepts only a pinned local observation containing source kind, source revision, source SHA-256, and capability keys. Each observed key must be classified as `supported`, `pass_through`, `blocked`, or `unavailable`. An upstream key that appears without classification is a failure. The tool does not fetch remote schemas and does not infer feature parity.

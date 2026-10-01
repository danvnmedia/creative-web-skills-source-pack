# Evidence Model

## States
- `pass`: the command/observation succeeded.
- `fail`: it ran and contradicted the claim.
- `blocked`: it could not complete (timeout/tool/credential/environment).
- `stale`: it passed previously but the workspace changed afterwards.

## Freshness
`record_evidence.py` hashes the current git revision plus working-tree changes/untracked content. A later code change makes prior evidence stale.

## Evidence quality hierarchy
1. real production/staging/user-flow observation;
2. real local browser/integration execution;
3. deterministic automated unit/contract/static checks;
4. source inspection;
5. model assertion/plan.

Use the highest practical layer needed by the claim. A lower layer cannot prove a higher-layer behavior.

# Evidence Architecture v5.5

v5.5 separates three identities that v5.4.x conflated:

- `product_source_digest`: content identity of product/runtime-relevant source. It excludes Harness runtime state and task lifecycle prose.
- `task_contract_digest`: objective, scope, traits, acceptance criteria, required checks, waivers/findings and release contract. Contract changes stale evidence.
- `lifecycle_state_digest`: STATE/RESUME/DECISIONS plus task lifecycle state. It proves continuity but does not invalidate product build evidence.

Evidence writers canonicalize task locators to `task.id`, write one atomic event file under `.ai/evidence/events/`, retain JSONL only as a rebuildable compatibility index, use contained collision-resistant log paths, record exact mutation paths, and classify blocked environment/external failures separately from product failures. A non-zero/blocked result never becomes pass.

Checkpoint promotion requires fresh source + task contract identity, successful producer exit, closed tool-call/result state and evidence lineage. Observable stdout is never promoted to a verified fact by wording alone.

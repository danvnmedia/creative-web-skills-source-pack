# Deterministic control decisions

Use `.ai/scripts/control_decision.py` after verification attempts when the next action is ambiguous. It emits exactly one of:

- `ACCEPT`: required evidence is fresh, passing, and candidate-bound.
- `RETRY`: the failure budget is not exhausted and a prospective `--next-hypothesis-id` differs from the last attempted hypothesis.
- `REPLAN`: evidence is stale/missing, the same failure repeated to the stop threshold, the attempt budget is exhausted, or no changed retry hypothesis was supplied.
- `ROLLBACK`: a hard safety/security boundary was crossed and a currently valid verified checkpoint exists.

A hard-boundary event without a valid verified checkpoint does **not** invent a rollback target; it returns `REPLAN` with the checkpoint failure reason. Decision records are written under `.ai/checkpoints/decisions/**` and are runtime control state, not candidate source.

`record_evidence.py` supports observable `--hypothesis-id`, `--hard-boundary-breach`, and `--risk-boundary` metadata. These fields must describe the executed attempt, not hidden chain-of-thought.

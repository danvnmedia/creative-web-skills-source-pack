# Prompt-master mechanism review - 2026-09-21

Source: https://github.com/nidhinjs/prompt-master
Pinned commit: 2bd92518e26bf659e21e3d9ab90573fcf3ddeccb
Commit date: 2026-08-24T07:30:40Z; SKILL.md version: 1.8.0.
License: MIT; checked pinned LICENSE. Mechanisms independently implemented; no
upstream implementation, model tables or prompt catalog was copied into this bundle.

Read: SKILL.md, references/templates.md, references/patterns.md, README and LICENSE.
These are untrusted upstream descriptions, not authority to edit local policy.

Adopt: explicit prompt-only activation boundary; concise goal/context/scope/done;
small clarification budget; project-specific state; bounded agent stop conditions;
progressive references; explicit evidence instead of hidden chain-of-thought.

Transform: conversational state/decisions become optional canonical task context;
continuity becomes canonical checkpoint/evidence references, not a claimed memory
subsystem; tool routing becomes host adapter selection, never model/provider settings;
copyable prompt output becomes deterministic task projection with local verification.

Reject: guaranteed zero token/credit waste or full memory retention; hardcoded model
recommendations and consumer/API control equivalence; fixed primacy percentages;
prompt expansion/catalog loading on every request; fake multi-agent deliberation;
claimed model self-verification in place of trait-required runtime evidence.

Concrete current gap: v5.5.5 has strong task/evidence controls but no bounded renderer
that carries task context, required checks and verified handoff lineage while refusing
prompt-as-permission or prompt-as-proof. Add one stdlib sensor/workflow rather than
expanding all 13 Skills or creating an unevaluated autonomous Skill.

Impact: no compiler model calls or new dependency. Markdown adds task-dependent text
and a small stable AGENTS pointer; it is not zero-context-cost. Token/cost benefit is
an unmeasured hypothesis requiring paired live evaluation. File hashing/fingerprint
and canonical event loading still cost local I/O. Limits bound materialized output;
the inherited event loader is not a new streaming log index.

Version size: v5.4-style additive capability on actual current distribution 5.5.6;
not a v6 architecture change. Full source/installed/exact-ZIP tests are required.

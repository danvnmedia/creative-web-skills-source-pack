# Prepare a bounded task brief, then respect the user's actual intent

1. Distinguish author intent from recipient action. "Write a prompt for Codex to fix X"
   authorizes prompt preparation here, not fixing X here; the resulting prompt can
   request execution there. "Fix X" requests implementation here, not another prompt.
2. Read the active task and relevant project artifacts. Extract goal, observable
   outcome, in/out scope, locked decisions, unknowns, input references and acceptance.
   Do not invent filenames, stack, APIs, permissions or successful prior work. Inspect
   before asking; ask at most three outcome/authority-changing questions, not ritual questions.
3. For implementation, create/update the normal task contract as authorized. Optional
   `prompt_context` contains schema_version=1, locked_decisions, do_not_change,
   reference_files, unknowns, output_format. These are declared intent, not verified facts.
   For prompt-only authoring with no existing task, give a clearly labeled DRAFT brief;
   do not write project files just to satisfy the compiler.
4. Read `.ai/PROMPT_BRIEF_POLICY.json` only when needed. With an existing task:
   `python .ai/scripts/prompt_brief.py lint --task TASK-ID`
   `python .ai/scripts/prompt_brief.py compile --task TASK-ID --host codex`
   Choose claude/gemini/antigravity for that actual receiver. `--receiver-mode plan-only`
   is ONLY when the recipient should plan, not because the author is preparing a prompt.
5. Default output is ephemeral. For authorized boundary persistence, opt in with
   `--save`; receive a content-addressed capsule under `.ai/checkpoints/briefs/`.
   `verify --capsule <relative-path>` must pass BEFORE using a saved capsule. A hash
   alone is not authorship or truth. Historical stale capsules remain inspectable,
   but cannot be reused as current guidance. Do not stage runtime state accidentally.
6. For `resume`/`handoff`, resolve a portable/audited task BEFORE fresh checkpoint
   evidence. The compiler calls canonical checkpoint validation; stale checkpoints
   block, failed/rejected events stay separate. Handoff without progress is allowed
   and explicitly labeled NOT_AVAILABLE. Handoff transfers no tool/sandbox authority.
7. `repair --hypothesis "..."` requires failed evidence and a changed, declared
   hypothesis. Run loop_guard as appropriate; the compiler does not prove a hypothesis
   changed semantically or authorize retries. Never turn failure-history omission into PASS.
8. For normal implementation, proceed after preparation. For prompt-only authoring,
   return one paste-ready brief and a short note on missing inputs. Do not keep
   rewriting prompts instead of doing requested work. No hidden-reasoning requests,
   hardcoded model/API controls, unmeasured token-saving guarantees or Skill activation claims.

The CLI is a deterministic serializer/validator, NOT a natural-language intent model.
The active agent extracts semantics. It does not execute commands from the prompt,
read referenced file contents into the prompt, change profiles, call APIs, or install anything.

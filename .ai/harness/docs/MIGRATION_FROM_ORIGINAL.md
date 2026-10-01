# Migration from the Original Multi-Agent Playbook

The original playbook remains valuable as a comprehensive reference. v3 changes the **operating assumption**, not the quality ambition.

## Kept from the original
- assumption vs evidence states;
- risk-first MVP;
- stage gates;
- artifact/source-of-truth ownership;
- vertical slices;
- security/privacy by design;
- verification ladder and regression gates;
- deployment SHA and production acceptance;
- monitoring/incident/backup discipline;
- no role-cosplay/consensus theater;
- human authority over consequential risk.

## Changed for real solo usage

### 1. Multi-agent team -> one primary agent with review lenses
The default is Codex doing implementation plus a separate verification/adversarial pass. Other models are fallback, not required team members.

### 2. Independent-review requirement -> risk-compensated verification
External independent review is not assumed to exist. High-risk work compensates with deterministic negative tests, security tooling, fresh adversarial inspection, and Human Gates for material risk. Never fake independence.

### 3. 17 stages -> compact lifecycle
Detailed handbook stages still exist conceptually, but runtime routing is compact and risk-adaptive so a patch does not go through product discovery ceremony.

### 4. Human approval at every stage -> consequential Human Gates
Codex continues autonomously through normal reversible work and only interrupts for decisions that materially affect scope, cost, data, security, irreversibility or release risk.

### 5. Handoff between specialists -> session-proof checkpoint
Because the likely failure mode is token/session exhaustion, `.ai/RESUME.md` is first-class. A new Codex/Gemini session can continue without reconstructing chat.

### 6. “Quality” becomes an explicit seven-dimension contract
Every applicable feature/release is evaluated across:
- user value;
- UX/UI;
- correctness;
- security/privacy;
- performance/scale;
- reliability/operations;
- maintainability.

This prevents an agent from optimizing only for code correctness while shipping a product that is slow, awkward, insecure, or impossible to operate.

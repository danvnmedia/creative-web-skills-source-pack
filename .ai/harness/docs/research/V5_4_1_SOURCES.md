# v5.4.1 public mechanism notes

This release reimplements small public mechanisms; it does not copy proprietary or paid content.

- Skill-eval projects: paired with/without-Skill comparisons, negative trigger cases, repeated runs, deterministic graders before judges, runtime identity capture, and measured token/duration/cost budgets.
- Trigger.dev `skills-evals`: exact published-package evaluation can expose loader/package failures hidden by source-tree tests. v5.4.1 therefore requires exact-artifact origins when loader/export behavior changes and re-extracts portable plugin releases before accepting them.
- Snyk/Cisco-style agent/Skill scanners and small low-star audit tools: use static pre-install inspection as a quarantine sensor. The local scanner remains independent and deterministic; external tools are optional.
- Tencent BrowserSkill-style containment: borrowing a real authenticated tab is an explicit scoped lease; disposable automation remains separate.
- Meta-harness/release-provenance work: bind exact artifacts with hashes/SBOM/witnesses and keep trust in signer identity out-of-band.

Before copying any external implementation detail, re-check its current license. The harness intentionally learns mechanisms and writes its own compact controls.

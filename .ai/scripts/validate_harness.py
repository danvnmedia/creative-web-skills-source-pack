#!/usr/bin/env python3
from pathlib import Path
import json, re
import sys
sys.dont_write_bytecode = True
from _common import configure_utf8_stdio, root_from_script, harness_context

EXPECTED = [
 '.ai/scripts/v556_regression_test.py','.ai/scripts/prompt_brief.py','.ai/PROMPT_BRIEF_POLICY.json','.ai/schemas/prompt_context.schema.json','.agents/workflows/brief-task.md','.ai/scripts/v555_regression_test.py','AGENTS.md','README.md','GEMINI.md','CLAUDE.md','ANTIGRAVITY.md','START_HERE_PROMPT.md','INSTALL_HARNESS.py','VERSION',
 '.ai/SOURCE_DISTRIBUTION.json','.ai/INSTALL_POLICY.json','.ai/PROJECT.md','.ai/STATE.json','.ai/COMMANDS.json','.ai/QUALITY.json','.ai/AI_PROVIDER_POLICY.json','.ai/SURFACE_OWNERSHIP.json','.ai/LEARNING_POLICY.json','.ai/RUNTIME_BUDGET.json','.ai/EXECUTION_POLICY.json','.ai/SKILL_EVAL_POLICY.json','.ai/SKILL_CATALOG_EVAL_POLICY.json','.ai/QUARANTINE_POLICY.json','.ai/SKILL_SECURITY_POLICY.json','.ai/HARNESS_SECURITY_POLICY.json','.ai/DETERMINISTIC_E2E_POLICY.json','.ai/HOST_SURFACE_POLICY.json','.ai/COMPACTION_POLICY.json','.ai/BROWSER_LEASE_POLICY.json','.ai/RELEASE_POLICY.json','.ai/WAIVER_POLICY.json','.ai/CONTROL_POLICY.json','.ai/MCP_POLICY.json','.ai/CANONICAL_SKILL_HASHES.json','.ai/HARNESS_MANIFEST.json',
 '.ai/TASK_TEMPLATE.json','.ai/FINGERPRINT_POLICY.json','.ai/CHECK_CATALOG.json','.ai/BROWSER_CAPABILITY_POLICY.json','.ai/schemas/task.schema.json','.ai/RESUME.md','.ai/DECISIONS.md','.ai/HANDOFF_TEMPLATE.md','.ai/evals/skill-routing.json','.ai/evals/skill-catalog-routing.json','.ai/checkpoints/README.md',
 '.ai/scripts/_common.py','.ai/scripts/verify_all.py','.ai/scripts/browser_capability.py','.ai/scripts/v551_regression_test.py','.ai/scripts/v553_regression_test.py','.ai/scripts/v554_regression_test.py','.ai/scripts/deterministic_regression_gate.py','.ai/scripts/skill_catalog_eval.py','.ai/scripts/host_surface_contract.py','.ai/scripts/install_plan.py','.ai/scripts/verify_installation.py','.ai/scripts/bootstrap_project.py','.ai/scripts/v545_regression_test.py','.ai/scripts/quarantine_scan.py','.ai/scripts/skill_security_gate.py','.ai/scripts/checkpoint_reverify.py','.ai/scripts/browser_lease.py','.ai/scripts/build_sbom.py','.ai/scripts/release_witness.py','.ai/scripts/repo_mapping.py','.ai/scripts/execution_profile.py','.ai/scripts/verified_checkpoint.py','.ai/scripts/skill_eval.py','.ai/scripts/export_agent_plugin.py','.ai/scripts/harness_doctor.py','.ai/scripts/control_decision.py','.ai/scripts/mcp_surface_pin.py',
 '.ai/scripts/release_doctor.py','.ai/scripts/v559_regression_test.py','.ai/scripts/v5510_regression_test.py','.ai/scripts/provider_route_budget.py','.ai/scripts/record_evidence.py','.ai/scripts/evidence_status.py','.ai/scripts/evidence_gate.py','.ai/scripts/validate_task.py','.ai/scripts/task_transition.py','.ai/scripts/candidate_preflight.py','.ai/scripts/harness.py','.ai/scripts/v550_regression_test.py','.ai/scripts/v550_snapshot_regression_test.py',
 '.ai/scripts/scan_external_urls.py','.ai/scripts/probe_urls.py','.ai/scripts/with_server.py',
 '.ai/scripts/browser_smoke.mjs','.ai/scripts/browser_flow.mjs','.ai/scripts/provider_policy_lint.py','.ai/scripts/completion_report.py',
 '.ai/scripts/close_task.py','.ai/scripts/accept_release.py','.ai/scripts/workspace_hygiene.py','.ai/scripts/verify_package.py','.ai/scripts/build_manifest.py','.ai/scripts/harness_ownership.py','.ai/scripts/surface_drift.py','.ai/scripts/harness_security.py','.ai/scripts/lesson_candidate.py','.ai/scripts/loop_guard.py','.ai/scripts/package_release.py','.ai/scripts/install_regression_test.py','.ai/scripts/v53_regression_test.py','.ai/scripts/v541_regression_test.py','.ai/scripts/v542_regression_test.py','.ai/scripts/v543_regression_test.py','.ai/scripts/v544_regression_test.py','.ai/scripts/lifecycle_regression_test.py','.ai/scripts/self_test.py','.ai/scripts/self_test_extended.py',
 'docs/MIGRATION_V5_5_8_TO_V5_5_9.md','docs/HUONG_DAN_V5_5_9_VI.md','docs/MIGRATION_V5_5_9_TO_V5_5_10.md','docs/HUONG_DAN_V5_5_10_VI.md','docs/research/V5_5_10_SOURCES.md','docs/harness/PRACTICAL_PRODUCT_LESSONS.md','docs/harness/CANDIDATE_CLOSURE.md','docs/harness/PACKAGING_RELEASE.md','docs/harness/INSTALL_OWNERSHIP.md','docs/harness/CROSS_HARNESS.md','docs/harness/SELF_IMPROVEMENT.md','docs/harness/HARNESS_SECURITY.md','docs/harness/ADAPTIVE_EXECUTION.md','docs/harness/SKILL_RUNTIME_ACCEPTANCE.md','docs/harness/TRUSTED_REPO_MAPPING.md','docs/harness/VERIFIED_PROGRESS.md','docs/harness/AGENT_PLUGIN_EXPORT.md','docs/harness/SKILL_QUARANTINE.md','docs/harness/BROWSER_LEASE.md','docs/harness/RELEASE_PROVENANCE.md','docs/harness/CONTENT_PINNED_WAIVERS.md','docs/harness/CONTROL_DECISIONS.md','docs/harness/MCP_SURFACE_PINNING.md','docs/harness/SOURCE_VS_INSTALLED_BOUNDARY.md','docs/harness/EVIDENCE_ARCHITECTURE_V5_5.md','docs/harness/OPERATOR_COMMAND_PLANE.md','docs/harness/CROSS_PLATFORM_RELIABILITY.md','docs/harness/SKILL_SECURITY_GATE.md','docs/harness/COMPACTION_TRUTH_BARRIER.md','docs/TRUTH_COMPLETENESS_V5_5_3.md','docs/SECURITY_COVERAGE_V5_5_4.md','docs/MIGRATION_V5_5_3_TO_V5_5_4.md','docs/research/V5_5_4_SOURCES.md','docs/MIGRATION_V5_5_2_TO_V5_5_3.md','docs/research/V5_5_3_SOURCES.md','docs/research/V5_3_SOURCES.md','docs/research/V5_4_1_SOURCES.md','docs/research/V5_4_2_SOURCES.md','docs/research/V5_4_3_SOURCES.md','docs/research/V5_4_4_SOURCES.md','docs/MIGRATION_V5_4_5_TO_V5_5_0.md','docs/MIGRATION_V5_5_0_TO_V5_5_1.md','docs/MIGRATION_V5_0_TO_V5_1.md','docs/MIGRATION_V5_1_TO_V5_2.md','docs/MIGRATION_V5_2_0_TO_V5_2_1.md','docs/MIGRATION_V5_2_1_TO_V5_3.md','docs/MIGRATION_V5_3_TO_V5_4_1.md','docs/MIGRATION_V5_4_1_TO_V5_4_2.md','docs/MIGRATION_V5_4_2_TO_V5_4_3.md','docs/MIGRATION_V5_4_3_TO_V5_4_4.md'
]

SKILLS = [
 'product-discovery','codebase-recon','feature-build','systematic-debugging','ui-ux-design',
 'runtime-verification','security-hardening','performance-reliability','ai-provider-routing',
 'ai-integration-verification','code-simplification','release-acceptance','harness-improvement'
]

def check_skill(path: Path, expected_name: str, errors: list[str]):
    if not path.exists():
        errors.append(f'missing skill: {path.relative_to(root_from_script())}')
        return
    text=path.read_text(encoding='utf-8')
    if len(text.splitlines()) > 500:
        errors.append(f'skill exceeds 500 lines: {expected_name}')
    if not text.startswith('---\n'):
        errors.append(f'missing YAML frontmatter: {expected_name}')
        return
    parts=text.split('---\n',2)
    if len(parts)<3:
        errors.append(f'invalid frontmatter: {expected_name}')
        return
    fm=parts[1].strip().splitlines()
    keys=[]; values={}
    for line in fm:
        if ':' in line:
            k,v=line.split(':',1); keys.append(k.strip()); values[k.strip()]=v.strip()
    if set(keys) != {'name','description'}:
        errors.append(f'{expected_name}: frontmatter must contain only name+description')
    if values.get('name') != expected_name:
        errors.append(f'{expected_name}: frontmatter name mismatch')
    if not values.get('description'):
        errors.append(f'{expected_name}: missing description')

def main():
    configure_utf8_stdio()
    root=root_from_script()
    context=harness_context(root)
    if context!='source':
        print(f'HARNESS VALIDATION: REFUSED — wrong boundary ({context}). This validator is source-distribution-only; run verify_installation.py --root . or harness.py verify inside an installed product repository.')
        raise SystemExit(2)
    errors=[]
    for rel in EXPECTED:
        if not (root/rel).exists(): errors.append(f'missing expected path: {rel}')
    for rel in ['.ai/STATE.json','.ai/COMMANDS.json','.ai/QUALITY.json','.ai/AI_PROVIDER_POLICY.json','.ai/TASK_TEMPLATE.json','.ai/SURFACE_OWNERSHIP.json','.ai/LEARNING_POLICY.json','.ai/RUNTIME_BUDGET.json','.ai/EXECUTION_POLICY.json','.ai/SKILL_EVAL_POLICY.json','.ai/SKILL_CATALOG_EVAL_POLICY.json','.ai/QUARANTINE_POLICY.json','.ai/SKILL_SECURITY_POLICY.json','.ai/HARNESS_SECURITY_POLICY.json','.ai/DETERMINISTIC_E2E_POLICY.json','.ai/HOST_SURFACE_POLICY.json','.ai/COMPACTION_POLICY.json','.ai/BROWSER_LEASE_POLICY.json','.ai/RELEASE_POLICY.json','.ai/WAIVER_POLICY.json','.ai/CONTROL_POLICY.json','.ai/MCP_POLICY.json','.ai/CANONICAL_SKILL_HASHES.json','.ai/evals/skill-routing.json','.ai/HARNESS_MANIFEST.json']:
        try: json.loads((root/rel).read_text(encoding='utf-8'))
        except Exception as e: errors.append(f'invalid JSON {rel}: {e}')
    for name in SKILLS:
        check_skill(root/f'.agents/skills/{name}/SKILL.md', name, errors)
    try:
        canonical=json.loads((root/'.ai/CANONICAL_SKILL_HASHES.json').read_text(encoding='utf-8'))
        if canonical.get('canonical_baseline')!='5.3.0' or canonical.get('skill_count')!=13:
            errors.append('canonical Skill hash contract must target v5.3.0 with 13 Skills')
        import hashlib
        for name, expected_hash in (canonical.get('sha256') or {}).items():
            actual=hashlib.sha256((root/f'.agents/skills/{name}/SKILL.md').read_bytes()).hexdigest()
            if actual!=expected_hash: errors.append(f'canonical v5.3 Skill drift: {name}')
    except Exception as exc:
        errors.append(f'canonical Skill hash validation failed: {exc}')
    try:
        task=json.loads((root/'.ai/TASK_TEMPLATE.json').read_text(encoding='utf-8'))
        quality=json.loads((root/'.ai/QUALITY.json').read_text(encoding='utf-8'))
        expected_traits={'user_facing_web','external_runtime_dependencies','ai_integration','security_sensitive','performance_sensitive','production_release','stateful_user_workflow','large_binary_data','truthful_claims','harness_modification','skill_modification','borrowed_browser_session','mcp_runtime'}
        missing_traits=expected_traits-set(task.get('traits',{}))
        if missing_traits: errors.append('task template missing traits: '+', '.join(sorted(missing_traits)))
        for section in ('execution_contract','experience_contract','state_contract','release'):
            if section not in task: errors.append(f'task template missing section: {section}')
        required_quality={'prompt-brief-contract','state-recovery','capacity-degradation','claim-contract','production-critical-flow','harness-security','surface-drift','package-contract','harness-self-test','skill-eval-contract','skill-eval-live','verified-progress','browser-lease','quarantine-contract','release-witness-contract','waiver-contract','control-decision-contract','mcp-surface-contract','mcp-surface-pin','install-collision-contract','source-installed-boundary','skill-security-contract','compaction-truth-contract','evidence-architecture-contract','cross-platform-reliability-contract','command-plane-contract','operational-lifecycle-contract','runtime-candidate-contract','check-catalog-contract','browser-capability-contract','security-analysis-completeness-contract','deterministic-e2e-complete','skill-catalog-confusion-contract','host-surface-contract','regression-environment-contract','git-machine-output-contract','newline-structure-contract'}
        configured={item for values in quality.get('trait_required_checks',{}).values() for item in values}
        configured.update(item for values in quality.get('profile_required_checks',{}).values() for item in values)
        if not required_quality.issubset(configured):
            errors.append('quality policy missing required Harness checks: '+', '.join(sorted(required_quality-configured)))
        if quality.get('version') != 12: errors.append('quality policy version must be 12')
        if task.get('schema_version') != 6: errors.append('task template schema_version must be 6')
        if (root/'VERSION').read_text(encoding='utf-8').strip() != '5.5.10': errors.append('VERSION must be 5.5.10')
    except Exception as exc:
        errors.append(f'v5.5.8 contract validation failed: {exc}')
    try:
        execution=json.loads((root/'.ai/EXECUTION_POLICY.json').read_text(encoding='utf-8'))
        if set(execution.get('profiles',{})) != {'native','portable','audited'}: errors.append('execution policy must define native/portable/audited')
        skill_eval=json.loads((root/'.ai/SKILL_EVAL_POLICY.json').read_text(encoding='utf-8'))
        accepted=set(skill_eval.get('activation_acceptance',{}).get('accepted_telemetry',[]))
        if not {'native','trace'}.issubset(accepted): errors.append('skill eval policy must accept native/trace telemetry')
        if 'self_report' in accepted: errors.append('skill eval policy must not accept self_report as activation proof')
        if skill_eval.get('version') != 3: errors.append('skill eval policy version must be 3')
        if not skill_eval.get('causal_acceptance',{}).get('budget'): errors.append('skill eval policy missing causal budget')
        if not quality.get('completion_policy',{}).get('borrowed_logged_in_browser_requires_lease'): errors.append('quality policy must require browser lease for borrowed logged-in sessions')
        if not quality.get('completion_policy',{}).get('content_pinned_waivers_required'): errors.append('quality policy must require content-pinned waivers')
        if not quality.get('completion_policy',{}).get('mcp_surface_changes_require_review'): errors.append('quality policy must require MCP surface review on drift')
        waiver=json.loads((root/'.ai/WAIVER_POLICY.json').read_text(encoding='utf-8'))
        if not waiver.get('stale_on_finding_change') or not waiver.get('expiry_is_fail_closed'): errors.append('waiver policy must fail closed on finding drift/expiry')
        control=json.loads((root/'.ai/CONTROL_POLICY.json').read_text(encoding='utf-8'))
        if control.get('decisions')!=['ACCEPT','RETRY','REPLAN','ROLLBACK']: errors.append('control policy decision set mismatch')
        mcp=json.loads((root/'.ai/MCP_POLICY.json').read_text(encoding='utf-8'))
        if not mcp.get('call_guard',{}).get('require_pinned_tool'): errors.append('MCP policy must require pinned tools')
        skill_security=json.loads((root/'.ai/SKILL_SECURITY_POLICY.json').read_text(encoding='utf-8'))
        if not skill_security.get('principles',{}).get('resource_limit_exhaustion_fails_closed') or not skill_security.get('principles',{}).get('static_only_must_be_labeled_static_only'): errors.append('Skill security policy must fail closed and truthfully label static-only scans')
        hsec=json.loads((root/'.ai/HARNESS_SECURITY_POLICY.json').read_text(encoding='utf-8'))
        if not hsec.get('principles',{}).get('analysis_incomplete_is_never_clean'): errors.append('Harness security completeness policy missing')
        de2e=json.loads((root/'.ai/DETERMINISTIC_E2E_POLICY.json').read_text(encoding='utf-8'))
        if not de2e.get('principles',{}).get('all_discovered_deterministic_regressions_are_required'): errors.append('deterministic E2E discovery policy missing')
        scat=json.loads((root/'.ai/SKILL_CATALOG_EVAL_POLICY.json').read_text(encoding='utf-8'))
        if not scat.get('principles',{}).get('target_is_separate_from_visible_catalog'): errors.append('Skill catalog eval policy missing target/catalog separation')
        hostsurf=json.loads((root/'.ai/HOST_SURFACE_POLICY.json').read_text(encoding='utf-8'))
        if not hostsurf.get('principles',{}).get('unknown_observed_capability_is_failure'): errors.append('host surface drift policy missing fail-closed unknown capability rule')
        compaction=json.loads((root/'.ai/COMPACTION_POLICY.json').read_text(encoding='utf-8'))
        cprinciples=compaction.get('principles',{})
        if not cprinciples.get('observed_output_is_never_verified_fact') or not cprinciples.get('resume_reverifies_checkpoint_before_use'): errors.append('compaction truth policy must reject observed-only claims and reverify resumes')
        if not quality.get('completion_policy',{}).get('untrusted_skill_requires_security_gate'): errors.append('quality policy must require Skill security gate')
        if not quality.get('completion_policy',{}).get('compaction_resume_requires_checkpoint_reverification'): errors.append('quality policy must require checkpoint reverification after compaction')
    except Exception as exc:
        errors.append(f'v5.4.4 policy validation failed: {exc}')
    try:
        marker=json.loads((root/'.ai/SOURCE_DISTRIBUTION.json').read_text(encoding='utf-8'))
        if marker.get('kind')!='codex-product-harness-source-distribution' or marker.get('version')!='5.5.10':
            errors.append('source distribution marker must identify v5.5.10 source tree')
        if (root/'.ai/HARNESS_INSTALL_STATE.json').exists():
            errors.append('source distribution must not contain installed-runtime ownership state')
        install=json.loads((root/'.ai/INSTALL_POLICY.json').read_text(encoding='utf-8'))
        if install.get('canonical_baseline')!='5.3.0': errors.append('install policy canonical baseline must remain v5.3.0')
        contract=install.get('apply_contract',{})
        if not contract.get('default_is_plan_only') or not contract.get('apply_requires_plan_digest') or not contract.get('compare_and_swap_before_each_write') or not contract.get('rollback_on_failure'):
            errors.append('install policy must enforce plan-only default + digest/CAS/rollback')
        protected=set(install.get('protected_project_paths',[]))
        if not {'README.md','VERSION','CHANGELOG.md','INSTALL_HARNESS.py'}.issubset(protected):
            errors.append('install policy missing protected generic project roots')
        mutable=set(install.get('mutable_seed_paths',[]))
        required_mutable={'.ai/PROJECT.md','.ai/STATE.json','.ai/COMMANDS.json','.ai/RESUME.md','.ai/DECISIONS.md'}
        if mutable != required_mutable:
            errors.append('install policy mutable_seed_paths must classify exactly the five runtime/project mutable seed surfaces')
        mcontract=install.get('mutable_seed_contract',{})
        if not mcontract.get('installer_never_overwrites_modified_seed') or not mcontract.get('verification_accepts_runtime_divergence') or not mcontract.get('immutable_managed_surfaces_remain_hash_strict'):
            errors.append('install policy missing runtime mutable seed safety contract')
        fp=json.loads((root/'.ai/FINGERPRINT_POLICY.json').read_text(encoding='utf-8'))
        if not fp.get('task_contract_digest',{}).get('includes_acceptance_criteria') or not fp.get('lifecycle_state_digest',{}).get('does_not_invalidate_product_evidence'):
            errors.append('v5.5 fingerprint policy must separate product/task/lifecycle truth')
        if not fp.get('runtime_candidate_digest',{}).get('does_not_invalidate_source_only_checks'):
            errors.append('v5.5.2 fingerprint policy must separate runtime-candidate identity from source-only evidence')
        catalog=json.loads((root/'.ai/CHECK_CATALOG.json').read_text(encoding='utf-8'))
        if catalog.get('harness_version')!='5.5.10' or not catalog.get('principles',{}).get('one_runner_executes_once_per_verify'):
            errors.append('v5.5.10 check catalog contract missing/damaged')
        provider_policy=json.loads((root/'.ai/AI_PROVIDER_POLICY.json').read_text(encoding='utf-8'))
        if provider_policy.get('version')!=3: errors.append('v5.5.10 source provider policy must use schema v3 actual-target budget semantics')
        browser_policy=json.loads((root/'.ai/BROWSER_CAPABILITY_POLICY.json').read_text(encoding='utf-8'))
        if browser_policy.get('executor_order')!=['connected-browser','project-local-playwright','approved-transient-playwright','unavailable']:
            errors.append('v5.5.2 browser capability executor order mismatch')
        if not (root/'.ai/schemas/task.schema.json').is_file(): errors.append('v5.5 task schema missing')
    except Exception as exc:
        errors.append(f'v5.5.10 install/source-boundary validation failed: {exc}')
    residue=[]
    for path in root.rglob('*'):
        if not path.is_file(): continue
        rel=path.relative_to(root)
        if any(part in {'.git','node_modules','.next','dist','build','coverage','.turbo','.cache'} for part in rel.parts): continue
        if '__pycache__' in rel.parts or path.suffix.lower() in {'.pyc','.pyo','.tmp','.bak','.orig'} or path.name in {'.DS_Store','Thumbs.db','desktop.ini'}:
            residue.append(rel.as_posix())
    if residue: errors.append('packaged generated residue: '+', '.join(sorted(residue)))
    # Catch the exact class of v4 packaging mistake: direct code-ticked harness paths in AGENTS must exist.
    text=(root/'AGENTS.md').read_text(encoding='utf-8')
    refs=set(re.findall(r'`((?:\.ai|\.agents)/[^`\s]+)`', text))
    for ref in refs:
        ref=ref.rstrip('.,;:)')
        if any(x in ref for x in ['<','>','*']): continue
        # Command examples may append args after file; regex stops at whitespace.
        p=root/ref
        if ref.endswith('/'):
            if not p.is_dir(): errors.append(f'AGENTS references missing directory: {ref}')
        elif not p.exists():
            # This one project-owned input is optional and has a shipped schema;
            # never invent a default design system or allow arbitrary missing refs.
            if ref == '.ai/UX_TOKENS.json':
                ux_schema=root/'.ai/schemas/ux-tokens.schema.json'
                if not ux_schema.is_file(): errors.append('optional UX_TOKENS schema missing')
                continue
            # Permit task placeholders and output paths that are created at runtime.
            if not (ref.startswith('.ai/tasks/') or ref.startswith('.ai/evidence/') or ref.startswith('.ai/checkpoints/') or ref == '.ai/REPO_MAP.json'):
                errors.append(f'AGENTS references missing path: {ref}')
    try:
        from _truth import read_json, sha
        preserved=read_json(root/'.ai/evals/canonical-v53-skills.json')
        if preserved.get('canonical_baseline')!='5.3.0' or len(preserved.get('files',[]))!=13:
            errors.append('canonical 13-Skill preservation contract damaged')
        for item in preserved.get('files',[]):
            if sha(root/item['path'])!=item['sha256']:
                errors.append('canonical Skill bytes changed: '+item['path'])
        for rel in ('PROMPT_BRIEF_POLICY.json','SKILL_RUNTIME_ACCEPTANCE.json','SKILL_EVAL_CONTRACT.json','AGENT_PLUGIN_POLICY.json','OPERATOR_EVENT_POLICY.json','MCP_ADVERSARIAL_POLICY.json','HARNESS_SECURITY_POLICY.json','DETERMINISTIC_E2E_POLICY.json','SKILL_CATALOG_EVAL_POLICY.json','HOST_SURFACE_POLICY.json'):
            if read_json(root/'.ai'/rel).get('schema_version')!=1:
                errors.append('unsupported truth contract: '+rel)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        errors.append('v5.5.10 truth contract failed: '+str(exc))
    if errors:
        print('HARNESS VALIDATION: FAIL')
        for e in errors: print(f'- {e}')
        raise SystemExit(1)
    print(f'HARNESS VALIDATION: PASS ({len(SKILLS)} skills, control plane + scripts present)')

if __name__=='__main__': main()

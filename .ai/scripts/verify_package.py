#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path, PurePosixPath
sys.dont_write_bytecode=True

EXPECTED_VERSION='5.5.10'
REQUIRED={
'.ai/scripts/release_doctor.py','.ai/scripts/v559_regression_test.py','.ai/scripts/v5510_regression_test.py','.ai/scripts/provider_route_budget.py','docs/MIGRATION_V5_5_8_TO_V5_5_9.md','docs/HUONG_DAN_V5_5_9_VI.md','docs/MIGRATION_V5_5_9_TO_V5_5_10.md','docs/HUONG_DAN_V5_5_10_VI.md','docs/research/V5_5_10_SOURCES.md','.ai/scripts/v557_regression_test.py','.ai/scripts/install_preflight.py','.ai/scripts/command_runtime.py','.ai/scripts/task_guidance.py','.ai/COMMAND_COMPATIBILITY.json','.ai/KNOWN_LEGACY_SURFACE_HASHES.json','.ai/TRAIT_SKILL_MAP.json','.ai/schemas/ux-tokens.schema.json','templates/task-feature.example.json','templates/task-release.example.json','templates/ux-tokens.example.json','docs/HARNESS_FEEDBACK_V5_5_7.md','docs/HUONG_DAN_V5_5_7_VI.md','docs/MIGRATION_V5_5_6_TO_V5_5_7.md',
'.ai/scripts/v556_regression_test.py','.ai/scripts/prompt_brief.py','.ai/PROMPT_BRIEF_POLICY.json','.ai/schemas/prompt_context.schema.json','.agents/workflows/brief-task.md','docs/MIGRATION_V5_5_5_TO_V5_5_6.md','.ai/scripts/v555_regression_test.py','VERSION','README.md','CHANGELOG.md','AGENTS.md','GEMINI.md','CLAUDE.md','ANTIGRAVITY.md','INSTALL_HARNESS.py','SBOM.spdx.json',
'.ai/SOURCE_DISTRIBUTION.json','.ai/INSTALL_POLICY.json',
'docs/MIGRATION_V5_2_1_TO_V5_3.md','docs/MIGRATION_V5_3_TO_V5_4_1.md','docs/MIGRATION_V5_4_1_TO_V5_4_2.md','docs/MIGRATION_V5_4_2_TO_V5_4_3.md','docs/MIGRATION_V5_4_3_TO_V5_4_4.md','docs/MIGRATION_V5_4_4_TO_V5_4_5.md','docs/MIGRATION_V5_4_5_TO_V5_5_0.md','docs/MIGRATION_V5_5_0_TO_V5_5_1.md','docs/MIGRATION_V5_5_2_TO_V5_5_3.md','docs/TRUTH_COMPLETENESS_V5_5_3.md','docs/SECURITY_COVERAGE_V5_5_4.md','docs/MIGRATION_V5_5_3_TO_V5_5_4.md','docs/research/V5_5_4_SOURCES.md','docs/research/V5_5_3_SOURCES.md',
'docs/harness/PACKAGING_RELEASE.md','docs/harness/INSTALL_OWNERSHIP.md','docs/harness/SKILL_RUNTIME_ACCEPTANCE.md','docs/harness/SKILL_QUARANTINE.md','docs/harness/BROWSER_LEASE.md','docs/harness/RELEASE_PROVENANCE.md','docs/harness/CONTENT_PINNED_WAIVERS.md','docs/harness/CONTROL_DECISIONS.md','docs/harness/MCP_SURFACE_PINNING.md','docs/harness/SOURCE_VS_INSTALLED_BOUNDARY.md','docs/harness/EVIDENCE_ARCHITECTURE_V5_5.md','docs/harness/OPERATOR_COMMAND_PLANE.md','docs/harness/CROSS_PLATFORM_RELIABILITY.md','docs/harness/SKILL_SECURITY_GATE.md','docs/harness/COMPACTION_TRUTH_BARRIER.md',
'docs/research/V5_4_1_SOURCES.md','docs/research/V5_4_2_SOURCES.md','docs/research/V5_4_3_SOURCES.md','docs/research/V5_4_4_SOURCES.md',
'.ai/HARNESS_MANIFEST.json','.ai/FINGERPRINT_POLICY.json','.ai/CHECK_CATALOG.json','.ai/BROWSER_CAPABILITY_POLICY.json','.ai/schemas/task.schema.json','.ai/evidence/README.md','.ai/checkpoints/README.md','.ai/SURFACE_OWNERSHIP.json','.ai/LEARNING_POLICY.json','.ai/RUNTIME_BUDGET.json','.ai/EXECUTION_POLICY.json','.ai/SKILL_EVAL_POLICY.json','.ai/QUARANTINE_POLICY.json','.ai/SKILL_SECURITY_POLICY.json','.ai/HARNESS_SECURITY_POLICY.json','.ai/DETERMINISTIC_E2E_POLICY.json','.ai/SKILL_CATALOG_EVAL_POLICY.json','.ai/HOST_SURFACE_POLICY.json','.ai/COMPACTION_POLICY.json','.ai/BROWSER_LEASE_POLICY.json','.ai/RELEASE_POLICY.json','.ai/WAIVER_POLICY.json','.ai/CONTROL_POLICY.json','.ai/MCP_POLICY.json','.ai/CANONICAL_SKILL_HASHES.json','.ai/evals/skill-routing.json','.ai/evals/skill-catalog-routing.json',
'.ai/scripts/validate_harness.py','.ai/scripts/deterministic_regression_gate.py','.ai/scripts/skill_catalog_eval.py','.ai/scripts/host_surface_contract.py','.ai/scripts/v553_regression_test.py','.ai/scripts/v554_regression_test.py','.ai/scripts/verify_all.py','.ai/scripts/browser_capability.py','.ai/scripts/v551_regression_test.py','.ai/scripts/validate_task.py','.ai/scripts/task_transition.py','.ai/scripts/candidate_preflight.py','.ai/scripts/harness.py','.ai/scripts/v550_regression_test.py','.ai/scripts/v550_snapshot_regression_test.py','.ai/scripts/verify_installation.py','.ai/scripts/install_plan.py','.ai/scripts/skill_eval.py','.ai/scripts/quarantine_scan.py','.ai/scripts/skill_security_gate.py','.ai/scripts/checkpoint_reverify.py','.ai/scripts/browser_lease.py','.ai/scripts/control_decision.py','.ai/scripts/mcp_surface_pin.py','.ai/scripts/build_sbom.py','.ai/scripts/release_witness.py','.ai/scripts/export_agent_plugin.py','.ai/scripts/package_release.py','.ai/scripts/v53_regression_test.py','.ai/scripts/v541_regression_test.py','.ai/scripts/v542_regression_test.py','.ai/scripts/v543_regression_test.py','.ai/scripts/v544_regression_test.py','.ai/scripts/v545_regression_test.py','.ai/scripts/self_test.py'}
FORBIDDEN_NAMES={'.DS_Store','Thumbs.db','desktop.ini'}
FORBIDDEN_SUFFIXES={'.pyc','.pyo','.tmp','.bak','.orig'}
FORBIDDEN_DIRS={'.git','node_modules','.next','dist','build','coverage','.turbo','.cache','__pycache__'}

def norm(n):
    n=n.replace('\\','/')
    while n.startswith('./'): n=n[2:]
    return n.lstrip('/')

def forbidden(n):
    p=PurePosixPath(norm(n))
    return any(x in FORBIDDEN_DIRS for x in p.parts) or p.name in FORBIDDEN_NAMES or p.suffix.lower() in FORBIDDEN_SUFFIXES

def payload_dir(path):
    d={}; names=[]
    for p in sorted(path.rglob('*')):
        if p.is_file():
            r=p.relative_to(path).as_posix(); names.append(r); d[r]=p.read_bytes()
    return d,names,[]

def payload_zip(path):
    d={}; names=[]; back=[]
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if i.is_dir(): continue
            if '\\' in i.filename: back.append(i.filename)
            n=norm(i.filename); names.append(n)
            if n in d: raise ValueError('duplicate archive entry: '+n)
            d[n]=z.read(i)
    return d,names,back

def text(d,n):
    try:return d[n].decode('utf-8-sig')
    except:return ''

def verify_manifest(d,errors):
    try:m=json.loads(text(d,'.ai/HARNESS_MANIFEST.json'))
    except Exception as e: errors.append('invalid manifest: '+str(e)); return
    if m.get('harness_version')!=EXPECTED_VERSION: errors.append('manifest version mismatch')
    for e in m.get('entries',[]):
        rel=norm(str(e.get('path',''))); data=d.get(rel)
        if data is None: errors.append('manifest-managed file missing: '+rel); continue
        if hashlib.sha256(data).hexdigest()!=e.get('sha256') or len(data)!=e.get('size'): errors.append('manifest mismatch: '+rel)

def verify_sbom(d,errors):
    try:s=json.loads(text(d,'SBOM.spdx.json'))
    except Exception as e: errors.append('invalid SBOM: '+str(e)); return
    if s.get('spdxVersion')!='SPDX-2.3': errors.append('SBOM must be SPDX-2.3')
    pk=(s.get('packages') or [{}])[0]
    if pk.get('versionInfo')!=EXPECTED_VERSION: errors.append('SBOM version mismatch')
    seen=set()
    for f in s.get('files',[]):
        rel=norm(str(f.get('fileName',''))); seen.add(rel); data=d.get(rel)
        if data is None: errors.append('SBOM file missing: '+rel); continue
        sums={x.get('algorithm'):x.get('checksumValue') for x in f.get('checksums',[])}
        if sums.get('SHA256')!=hashlib.sha256(data).hexdigest(): errors.append('SBOM hash mismatch: '+rel)
    if any(r=='.ai/REPO_MAP.json' or (r.startswith('.ai/checkpoints/') and r!='.ai/checkpoints/README.md') for r in seen): errors.append('SBOM includes runtime-state path')

def main():
    ap=argparse.ArgumentParser(description='Verify a Harness source distribution or exact release ZIP. Installed product repositories are deliberately out of scope.')
    ap.add_argument('--path',required=True); ap.add_argument('--out'); a=ap.parse_args(); target=Path(a.path).resolve(); errors=[]
    if target.is_dir() and (target/'.ai/HARNESS_INSTALL_STATE.json').is_file() and not (target/'.ai/SOURCE_DISTRIBUTION.json').is_file():
        errors.append('installed product repository is not a Harness source package; use .ai/scripts/verify_installation.py')
        d={}; names=[]; back=[]; kind='installed-directory'; digest=None
    elif target.is_dir(): kind='source-directory'; d,names,back=payload_dir(target); digest=None
    elif target.is_file() and target.suffix.lower()=='.zip': kind='zip'; d,names,back=payload_zip(target); digest=hashlib.sha256(target.read_bytes()).hexdigest()
    else: raise SystemExit('PACKAGE VERIFY: FAIL - unsupported path')
    if kind!='installed-directory':
        missing=sorted(REQUIRED-set(d))
        if missing: errors.append('missing required files: '+', '.join(missing))
        residue=sorted(x for x in names if forbidden(x))
        if residue: errors.append('forbidden source/package residue: '+', '.join(residue[:30]))
        if back: errors.append('ZIP entries use non-portable backslash separators: '+', '.join(back[:10]))
        runtime=[x for x in d if x=='.ai/REPO_MAP.json' or x=='.ai/HARNESS_INSTALL_STATE.json' or (x.startswith('.ai/checkpoints/') and x!='.ai/checkpoints/README.md')]
        if runtime: errors.append('packaged runtime state: '+', '.join(runtime[:10]))
        version=text(d,'VERSION').strip(); head=(text(d,'README.md').splitlines() or [''])[0]
        if version!=EXPECTED_VERSION: errors.append(f'VERSION is {version!r}, expected {EXPECTED_VERSION!r}')
        if head!=f'# Codex Product Harness v{EXPECTED_VERSION}': errors.append('README heading mismatch: '+repr(head))
        if f'## {EXPECTED_VERSION}' not in text(d,'CHANGELOG.md'): errors.append('CHANGELOG lacks '+EXPECTED_VERSION)
        try: marker=json.loads(text(d,'.ai/SOURCE_DISTRIBUTION.json'))
        except Exception as exc: marker={}; errors.append('invalid source distribution marker: '+str(exc))
        if marker.get('kind')!='codex-product-harness-source-distribution' or marker.get('version')!=EXPECTED_VERSION: errors.append('source distribution marker mismatch')
        if len([x for x in d if x.startswith('.agents/skills/') and x.endswith('/SKILL.md')])!=13: errors.append('expected exactly 13 packaged skills')
        verify_manifest(d,errors); verify_sbom(d,errors)
    else:
        version=''
        runtime=[]; back=[]
    report={'schema_version':4,'status':'pass' if not errors else 'fail','path':str(target),'kind':kind,'version':version,'file_count':len(d),'sha256':digest,'portable_zip_paths':not back,'runtime_state_excluded':not runtime,'errors':errors}
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out: Path(a.out).write_text(rendered,encoding='utf-8')
    print(rendered,end='')
    if errors: raise SystemExit(1)
if __name__=='__main__': main()

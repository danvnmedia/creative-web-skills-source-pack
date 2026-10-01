#!/usr/bin/env python3
"""v5.5.7 field-feedback regressions. Local protocols, not live product/Skill acceptance."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
import _common as c
import command_runtime as cr
import install_plan as ip
import install_preflight as pre
import task_guidance as tg
import validate_task as vt
import with_server as ws
ROOT=Path(__file__).resolve().parents[2]
PY=sys.executable
IS_SOURCE=(ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file()


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data if isinstance(data,bytes) else (json.dumps(data,indent=2)+'\n').encode())


def run(argv,cwd=None,expected=0,timeout=25,env=None):
    p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if p.returncode!=expected: raise AssertionError(f'{argv}: exit={p.returncode}, expected={expected}\n{p.stdout}\n{p.stderr}')
    return p


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='v557-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def task(self):
        t=json.loads((ROOT/'.ai/TASK_TEMPLATE.json').read_text());t.update(id='TASK-FIELD',status='IN_PROGRESS',objective='protocol fixture',user_outcome='verify invariants')
        return t
    def init_git(self,p):
        run(['git','init','-q',str(p)])
    def commit(self,p):
        env=os.environ.copy();env.update(GIT_AUTHOR_NAME='Fixture',GIT_COMMITTER_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',GIT_COMMITTER_EMAIL='fixture@example.invalid')
        run(['git','-c','core.autocrlf=false','add','.'],cwd=p,env=env)
        run(['git','-c','commit.gpgsign=false','commit','-qm','fixture'],cwd=p,env=env)


class PreflightTests(Tmp):
    def test_finds_ci_script_and_provides_installed_alternative(self):
        write(self.root/'.github/workflows/ci.yml',b'run: python .ai/scripts/validate_harness.py\n')
        r=pre.collect(ROOT,self.root);self.assertEqual(r['references'][0]['kind'],'source_only')
        self.assertIn('verify_installation',r['references'][0]['replacement']);self.assertFalse(r['mutated'])
    def test_self_test_presence_is_supported_not_blanket_banned(self):
        write(self.root/'Makefile',b'check:\n\tpython .ai/scripts/self_test.py\n')
        self.assertEqual(pre.collect(ROOT,self.root)['references'][0]['kind'],'supported_context_review')
    def test_package_path_requires_context_review_not_automatic_rewrite(self):
        raw=b'python .ai/scripts/verify_package.py --path ../trusted.zip\n';write(self.root/'Makefile',raw)
        r=pre.collect(ROOT,self.root);self.assertEqual(r['references'][0]['kind'],'explicit_source_path');self.assertEqual((self.root/'Makefile').read_bytes(),raw)
    def test_no_false_match_for_similar_script_name(self):
        write(self.root/'Makefile',b'old_validate_harness.py.bak\n')
        self.assertFalse(pre.collect(ROOT,self.root)['references'])
    def test_env_and_node_modules_not_scanned(self):
        write(self.root/'.env',b'validate_harness.py');write(self.root/'node_modules/test.md',b'validate_harness.py')
        r=pre.collect(ROOT,self.root);self.assertFalse(r['references']);self.assertEqual(r['files_read'],0)
    def test_large_file_is_partial_not_clean(self):
        write(self.root/'README.md',b'x'*(pre.MAX_FILE_BYTES+1));r=pre.collect(ROOT,self.root)
        self.assertEqual(r['status'],'partial');self.assertTrue(r['limits'])
    def test_symlink_directory_is_not_followed(self):
        out=self.root/'outside';out.mkdir();write(out/'evil.yml',b'validate_harness.py')
        try:(self.root/'.github').symlink_to(out,target_is_directory=True)
        except OSError:self.skipTest('symlink privilege unavailable')
        r=pre.collect(ROOT,self.root);self.assertEqual(r['status'],'partial');self.assertFalse(r['references'])
    def test_unknown_outside_agent_text_preserved(self):
        raw=b'# Product instructions\r\n';write(self.root/'AGENTS.md',raw)
        r=pre.collect(ROOT,self.root);self.assertEqual(r['legacy_surfaces'][0]['action'],'preserve_unknown_project_text');self.assertEqual((self.root/'AGENTS.md').read_bytes(),raw)
    def test_known_legacy_identification_does_not_authorize_delete(self):
        # The exact source entry can be known; recognition remains advisory only.
        raw=(ROOT/'AGENTS.md').read_bytes() if IS_SOURCE else b'# unchanged user text\n'
        write(self.root/'AGENTS.md',raw)
        r=pre.collect(ROOT,self.root);self.assertFalse(r['legacy_surfaces'][0]['automatic_delete_authorized'])
    def test_ignored_state_warns_clean_checkout_loss(self):
        self.init_git(self.root);write(self.root/'.gitignore',b'.ai/HARNESS_INSTALL_STATE.json\n');write(self.root/pre.STATE,{'schema_version':3})
        r=pre.collect(ROOT,self.root);self.assertTrue(r['git_state']['ignored']);self.assertFalse(r['git_state']['tracked'])
        self.assertTrue(any('CI_INSTALL_STATE_IGNORED' in w for w in r['warnings']))
    def test_tracked_state_not_misreported_as_missing(self):
        self.init_git(self.root);write(self.root/pre.STATE,{'schema_version':3});run(['git','add',pre.STATE],cwd=self.root)
        r=pre.collect(ROOT,self.root);self.assertTrue(r['git_state']['tracked']);self.assertFalse(r['git_state']['fresh_checkout_missing_state'])
    def test_directory_walk_budget_is_explicit_partial(self):
        for i in range(5): (self.root/'.github'/str(i)).mkdir(parents=True)
        with patch.object(pre,'MAX_ENTRIES',3): r=pre.collect(ROOT,self.root)
        self.assertEqual(r['status'],'partial');self.assertTrue(any(x['reason']=='directory_entry_budget' for x in r['limits']))
    def test_finding_budget_is_explicit_partial(self):
        write(self.root/'Makefile',b'validate_harness.py\n'*8)
        with patch.object(pre,'MAX_FINDINGS',3): r=pre.collect(ROOT,self.root)
        self.assertEqual(len(r['references']),3);self.assertEqual(r['status'],'partial')
    def test_git_errors_not_reported_as_tracked_state(self):
        with patch.object(pre,'git',return_value=(-1,'')):
            self.assertIsNone(pre.git_state(self.root)['tracked'])


@unittest.skipUnless(IS_SOURCE,'source-only install/lifecycle fixture; use source release lane')
class InstallTests(Tmp):
    def installed(self):
        p=self.root/'product';p.mkdir()
        write(p/'README.md',b'Product README\r\n');write(p/'VERSION',b'Product-1\r\n')
        write(p/'AGENTS.md',b'Project instructions\r\n');write(p/'.gitattributes',b'# Product attrs\r\n*.png binary\r\n')
        plan,_=ip.build_plan(ROOT,p);self.assertTrue(plan['safe_to_apply']);ip.apply_plan(ROOT,p,plan['plan_digest']);return p
    def test_real_evidence_closure_roundtrip_preserves_runtime_checks(self):
        # Deterministic lifecycle protocol fixture, not a real browser/production run.
        p=self.installed();self.init_git(p);t=self.task()
        t['execution_contract'].update(profile='native',resolved_profile='native')
        t['verification']['required_checks']=['runtime-browser','critical-flow','external-probe']
        write(p/'.ai/tasks/TASK-FIELD.json',t);self.commit(p)
        for name in t['verification']['required_checks']:
            run([PY,'.ai/scripts/record_evidence.py','--task','TASK-FIELD','--check',name,'--',PY,'-c',"print('DETERMINISTIC PROTOCOL FIXTURE ONLY')"],cwd=p)
        events_before=c.load_events(p/'.ai/evidence/events.jsonl')
        run([PY,'.ai/scripts/close_task.py','--task','TASK-FIELD','--production-url','https://fixture.example.invalid'],cwd=p)
        result=run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-FIELD'],cwd=p)
        self.assertIn('3 required checks',result.stdout)
        self.assertEqual(events_before,c.load_events(p/'.ai/evidence/events.jsonl'))
        repeated=run([PY,'.ai/scripts/close_task.py','--task','TASK-FIELD'],cwd=p,expected=1)
        self.assertIn('new successor task',repeated.stderr)
        transitioned=run([PY,'.ai/scripts/task_transition.py','--task','TASK-FIELD','--to','IN_PROGRESS'],cwd=p,expected=1)
        self.assertIn('terminal',transitioned.stderr)
        # Real change must remain stale, even though a closure receipt is no longer a runtime change.
        (p/'README.md').write_bytes(b'Changed product source')
        bad=run([PY,'.ai/scripts/evidence_gate.py','--task','TASK-FIELD'],cwd=p,expected=1)
        self.assertIn('non-closure',bad.stdout)
    def test_optional_ux_schema_does_not_allow_unknown_missing_reference(self):
        clone=self.root/'source';c.copy_source_tree(ROOT,clone,ignore=shutil.ignore_patterns('.git','__pycache__'))
        self.assertFalse((clone/'.ai/UX_TOKENS.json').exists())
        run([PY,'.ai/scripts/validate_harness.py'],cwd=clone)
        with (clone/'AGENTS.md').open('a') as f:f.write('\n`.ai/UNKNOWN_MISSING.json`\n')
        bad=run([PY,'.ai/scripts/validate_harness.py'],cwd=clone,expected=1)
        self.assertIn('references missing path: .ai/UNKNOWN_MISSING.json',bad.stdout)
    def test_accept_release_missing_manifest_names_path(self):
        p=self.installed();t=self.task();t['traits']['production_release']=True;t['status']='COMPLETE'
        write(p/'.ai/tasks/TASK-FIELD.json',t)
        result=run([PY,'.ai/scripts/accept_release.py','--task','TASK-FIELD','--production-url','https://fixture.example.invalid','--deployed-revision','a'*40,'--ci-url','https://ci.example.invalid'],cwd=p,expected=1)
        self.assertIn('closure-TASK-FIELD.json',result.stderr)
        self.assertIn('.ai',result.stderr)
    def test_scoped_attributes_preserve_outside_bytes(self):
        p=self.installed();raw=(p/'.gitattributes').read_bytes()
        self.assertTrue(raw.startswith(b'# Product attrs\r\n*.png binary\r\n'))
        found=ip.find_block(raw,'git-attributes');self.assertIsNotNone(found)
        self.assertNotIn(b'* text',found[2]);self.assertIn(b'/.agents/skills/ui-ux-design/SKILL.md',found[2])
        self.assertNotIn(b'"/README.md"',found[2]);self.assertNotIn(b'"/VERSION"',found[2])
    def test_preflight_change_invalidates_plan_before_mutation(self):
        p=self.root/'product';p.mkdir();write(p/'.github/workflows/ci.yml',b'run: old\n')
        plan,_=ip.build_plan(ROOT,p);write(p/'.github/workflows/ci.yml',b'run: new\n')
        with self.assertRaisesRegex(RuntimeError,'stale'):ip.apply_plan(ROOT,p,plan['plan_digest'])
        self.assertFalse((p/'.ai/QUALITY.json').exists())
    def test_crlf_requires_explicit_plan_and_repairs_exact_bytes(self):
        p=self.installed();path=p/'.agents/skills/ui-ux-design/SKILL.md';expected=path.read_bytes();path.write_bytes(expected.replace(b'\n',b'\r\n'))
        normal,_=ip.build_plan(ROOT,p);self.assertFalse(normal['safe_to_apply'])
        fixed,_=ip.build_plan(ROOT,p,repair_eol=True);self.assertTrue(fixed['safe_to_apply'])
        with self.assertRaisesRegex(RuntimeError,'stale'):ip.apply_plan(ROOT,p,fixed['plan_digest'])
        ip.apply_plan(ROOT,p,fixed['plan_digest'],repair_eol=True);self.assertEqual(path.read_bytes(),expected)
        run([PY,str(p/'.ai/scripts/verify_installation.py'),'--root',str(p)])
    def test_eol_option_cannot_adopt_content_mutation(self):
        p=self.installed();path=p/'.agents/skills/ui-ux-design/SKILL.md';path.write_bytes(path.read_bytes().replace(b'\n',b'\r\n')+b'new content\r\n')
        self.assertFalse(ip.build_plan(ROOT,p,repair_eol=True)[0]['safe_to_apply'])
    def test_eol_option_cannot_remove_bom(self):
        p=self.installed();path=p/'.agents/skills/ui-ux-design/SKILL.md';path.write_bytes(b'\xef\xbb\xbf'+path.read_bytes().replace(b'\n',b'\r\n'))
        self.assertFalse(ip.build_plan(ROOT,p,repair_eol=True)[0]['safe_to_apply'])
    def test_managed_block_crlf_repair_preserves_external_text(self):
        p=self.installed();path=p/'AGENTS.md';raw=path.read_bytes();b=ip.find_block(raw,'agents');outside_before=raw[:b[0]];outside_after=raw[b[1]:]
        path.write_bytes(outside_before+b[2].replace(b'\n',b'\r\n')+outside_after)
        plan,_=ip.build_plan(ROOT,p,repair_eol=True);self.assertTrue(plan['safe_to_apply']);ip.apply_plan(ROOT,p,plan['plan_digest'],repair_eol=True)
        now=path.read_bytes();b2=ip.find_block(now,'agents');self.assertEqual(now[:b2[0]],outside_before);self.assertEqual(now[b2[1]:],outside_after)
    def test_clean_git_checkout_autocrlf_preserves_13_skills_and_state(self):
        p=self.installed();self.init_git(p)
        write(p/'.gitignore',b'.ai/checkpoints/*\n!.ai/checkpoints/README.md\n.ai/evidence/*\n!.ai/evidence/README.md\n');self.commit(p)
        clone=self.root/'clone';run(['git','-c','core.autocrlf=true','clone','-q',str(p),str(clone)])
        for source in (ROOT/'.agents/skills').glob('*/SKILL.md'):
            self.assertEqual((clone/source.relative_to(ROOT)).read_bytes(),source.read_bytes())
        self.assertTrue((clone/pre.STATE).exists())
        run([PY,str(clone/'.ai/scripts/verify_installation.py'),'--root',str(clone)])
    def test_git_attribute_conflict_does_not_replace_project_policy(self):
        p=self.installed();path=p/'.gitattributes';raw=path.read_bytes();path.write_bytes(raw.replace(b'-filter',b'filter=custom',1))
        self.assertFalse(ip.build_plan(ROOT,p)[0]['safe_to_apply']);self.assertIn(b'filter=custom',path.read_bytes())
    def test_repair_retains_old_runtime_evidence(self):
        p=self.installed();write(p/'.ai/evidence/old.json',b'{"old":true}\r\n');before=(p/'.ai/STATE.json').read_bytes()
        (p/'.ai/QUALITY.json').unlink();plan,_=ip.build_plan(ROOT,p);ip.apply_plan(ROOT,p,plan['plan_digest'])
        self.assertEqual((p/'.ai/STATE.json').read_bytes(),before);self.assertEqual((p/'.ai/evidence/old.json').read_bytes(),b'{"old":true}\r\n')
    def test_transaction_rolls_back_attributes_and_state(self):
        p=self.installed();(p/'.ai/QUALITY.json').unlink();(p/'.ai/TRAIT_SKILL_MAP.json').unlink()
        before={x.relative_to(p).as_posix():x.read_bytes() for x in p.rglob('*') if x.is_file() and '.ai/checkpoints/' not in x.relative_to(p).as_posix()}
        plan,_=ip.build_plan(ROOT,p);original=ip._write_atomic;count=[0]
        def fail(path,data):
            count[0]+=1
            if count[0]==2:raise OSError('injected transaction error')
            return original(path,data)
        with patch.object(ip,'_write_atomic',side_effect=fail):
            with self.assertRaises(OSError):ip.apply_plan(ROOT,p,plan['plan_digest'])
        after={x.relative_to(p).as_posix():x.read_bytes() for x in p.rglob('*') if x.is_file() and '.ai/checkpoints/' not in x.relative_to(p).as_posix()}
        self.assertEqual(before,after)


class RuntimeIdentityTests(Tmp):
    def setUp(self):super().setUp();write(self.root/'app.py',b'pass\n');self.t=self.task()
    def test_adding_closure_does_not_invalidate_unchanged_runtime(self):
        before=c.runtime_candidate_digest(self.root,self.t)
        write(c.closure_manifest_path(self.root,self.t['id']),{'candidate_sha':'a'*40,'candidate_fingerprint':c.product_source_digest(self.root),'release':{'production_url':'https://example.invalid'}})
        self.assertEqual(c.runtime_candidate_digest(self.root,self.t),before)
    def test_lifecycle_status_does_not_invalidate_runtime(self):
        before=c.runtime_candidate_digest(self.root,self.t);self.t['status']='COMPLETE';self.t['closure']={'closed_at':'now'}
        self.assertEqual(c.runtime_candidate_digest(self.root,self.t),before)
    def test_runtime_changes_still_invalidate_every_bound_field(self):
        before=c.runtime_candidate_digest(self.root,self.t)
        for key in ('candidate_revision','deployed_revision','revision_marker','artifact_sha256','deployment_id','production_url'):
            t=copy.deepcopy(self.t);t['release'][key]='changed'
            with self.subTest(key=key):self.assertNotEqual(c.runtime_candidate_digest(self.root,t),before)
    def test_source_change_still_invalidates_runtime(self):
        before=c.runtime_candidate_digest(self.root,self.t);write(self.root/'app.py',b'print(1)\n');self.assertNotEqual(c.runtime_candidate_digest(self.root,self.t),before)
    def test_url_task_contract_stays_bound(self):
        before=c.task_contract_digest(self.t);self.t['release']['production_url']='https://other.invalid';self.assertNotEqual(c.task_contract_digest(self.t),before)
    def test_policy_excludes_only_closure_receipt_not_environment(self):
        fields=json.loads((ROOT/'.ai/FINGERPRINT_POLICY.json').read_text())['runtime_candidate_digest']['includes']
        self.assertIn('release.production_url',fields);self.assertIn('release.deployed_revision',fields);self.assertFalse(any(x.startswith('closure.') for x in fields))
    def test_old_task_states_not_reopened(self):
        import task_transition
        self.assertEqual(task_transition.ALLOWED['COMPLETE'],set())
    def test_closure_missing_path_error_and_guidance_present(self):
        source=(ROOT/'.ai/scripts/accept_release.py').read_text();self.assertIn('closure_manifest_path(root',source)
        close=(ROOT/'.ai/scripts/close_task.py').read_text();self.assertIn('release-acceptance/SKILL.md',close);self.assertIn('--ephemeral',close);self.assertIn('NOT persisted evidence',close)


class TaskGuidanceTests(Tmp):
    def test_schema_enum_and_validator_share_authority(self):
        enum=json.loads((ROOT/'.ai/schemas/task.schema.json').read_text())['properties']['mode']['enum'];self.assertEqual(set(enum),vt.ALLOWED_MODES)
    def test_invalid_patch_explains_modes(self):
        t=self.task();t['mode']='PATCH';errors=vt.errors_for(t);self.assertTrue(any('allowed:' in x and 'BUGFIX' in x for x in errors))
    def test_all_supported_modes_accepted(self):
        for mode in vt.ALLOWED_MODES:
            t=self.task();t['mode']=mode;self.assertFalse(vt.errors_for(t))
    def test_unknown_checks_warn_but_remain_required(self):
        t=self.task();t['verification']['required_checks']=['project-custom-check'];g=tg.guidance(ROOT,t)
        self.assertIn('project-custom-check',g['unregistered_checks']);self.assertIn('project-custom-check',c.derive_required_checks(t,json.loads((ROOT/'.ai/QUALITY.json').read_text())))
    def test_release_trait_provides_non_telemetry_skill_hint(self):
        t=self.task();t['traits']['production_release']=True;g=tg.guidance(ROOT,t)
        self.assertIn('release-acceptance',g['recommended_skills']);self.assertFalse(g['is_activation_evidence']);self.assertTrue(g['advisory_only'])
    def test_map_references_only_existing_canonical_skills(self):
        p=json.loads((ROOT/'.ai/TRAIT_SKILL_MAP.json').read_text())
        for names in p['mapping'].values():
            for name in names:self.assertTrue((ROOT/'.agents/skills'/name/'SKILL.md').is_file())
    def test_feature_and_release_examples_validate(self):
        base=ROOT/'templates' if IS_SOURCE else ROOT/'.ai/harness/templates'
        for mode in ('feature','release'):
            t=json.loads((base/f'task-{mode}.example.json').read_text());self.assertFalse(vt.errors_for(t));self.assertEqual(t['status'],'READY');self.assertTrue(t['acceptance_criteria'])
    def test_ux_example_valid_structure_not_acceptance(self):
        base=ROOT/'templates' if IS_SOURCE else ROOT/'.ai/harness/templates'
        self.assertFalse(tg.ux_errors(json.loads((base/'ux-tokens.example.json').read_text())))
    def test_ux_malformed_and_boolean_spacing_rejected(self):
        self.assertTrue(tg.ux_errors([]))
        base=ROOT/'templates' if IS_SOURCE else ROOT/'.ai/harness/templates'
        t=json.loads((base/'ux-tokens.example.json').read_text());t['spacing_px']['sm']=True;self.assertTrue(tg.ux_errors(t))
    def test_ux_unknown_keys_and_unbounded_strings_rejected(self):
        base=ROOT/'templates' if IS_SOURCE else ROOT/'.ai/harness/templates'
        t=json.loads((base/'ux-tokens.example.json').read_text());t['new_field']='x';t['colors']['text']='x'*500
        self.assertGreaterEqual(len(tg.ux_errors(t)),2)


class ModeInputTests(Tmp):
    def test_invalid_mode_types_are_errors_not_tracebacks(self):
        for value in ([], {}, 1, '', None):
            t=self.task();t['mode']=value
            self.assertTrue(any('mode enum invalid; allowed:' in e for e in vt.errors_for(t)))


class WindowsCommandTests(Tmp):
    def fake_cmd(self):
        system=self.root/'Windows';write(system/'System32/cmd.exe',b'not executed')
        exe=self.root/'Program Files/npm.cmd';write(exe,b'not executed');return system,exe
    def test_batch_resolves_with_explicit_system_host(self):
        system,exe=self.fake_cmd()
        with patch.object(cr.shutil,'which',return_value=str(exe)):
            argv=cr.resolve_argv(['npm','run','dev'],windows=True,env={'SystemRoot':str(system),'PATH':''})
        self.assertIsInstance(argv,str);self.assertIn(' /d /s /c ',argv);self.assertIn('npm.cmd',argv);self.assertNotIn('\\"',argv);self.assertTrue(argv.endswith('run dev"'))
    def test_batch_metacharacters_fail_closed(self):
        system,exe=self.fake_cmd()
        for value in ('a&b','%PATH%','!x!','x|y','x\nnext','x"y'):
            with patch.object(cr.shutil,'which',return_value=str(exe)):
                with self.assertRaisesRegex(ValueError,'policy denied'):cr.resolve_argv(['npm',value],windows=True,env={'SystemRoot':str(system)})
    def test_powershell_never_policy_bypassed(self):
        with patch.object(cr.shutil,'which',return_value='example.ps1'):
            with self.assertRaisesRegex(ValueError,'will not bypass'):cr.resolve_argv(['example.ps1'],windows=True)
    def test_missing_executable_is_actionable(self):
        with patch.object(cr.shutil,'which',return_value=None):
            with self.assertRaisesRegex(ValueError,'COMMAND_UNAVAILABLE'):cr.resolve_argv(['missing'],windows=True)
    def test_native_executable_keeps_argument_array(self):
        with patch.object(cr.shutil,'which',return_value='node.exe'):
            self.assertEqual(cr.resolve_argv(['node','x & y'],windows=True),['node.exe','x & y'])
    def test_posix_never_implicitly_shells(self):
        self.assertEqual(cr.resolve_argv(['echo','x & y'],windows=False),['echo','x & y'])
    def test_missing_command_capture_is_recordable_not_traceback(self):
        import record_evidence as evidence
        result=evidence._run_stream(['nonexistent-harness-fixture-command'],self.root,1,self.root/'log',1024)
        self.assertEqual(result[0],127);self.assertIn('COMMAND_UNAVAILABLE',result[1]);self.assertEqual(evidence._classify_failure(result[0],False,result[1])[0],'blocked')
    @unittest.skipUnless(os.name=='nt','native Windows cmd.exe execution not available on this host')
    def test_native_windows_cmd_space_argument(self):
        file=self.root/'fixture.cmd';write(file,b'@echo off\r\necho %~1\r\n')
        p=run(cr.resolve_argv([str(file),'space value']));self.assertIn('space value',p.stdout)


class ServerTests(Tmp):
    def command(self,p,args):
        return [PY,str(ROOT/'.ai/scripts/with_server.py'),'--port',str(p),*args,'--',PY,'-c',f'from pathlib import Path;Path({str(self.root/"verified")!r}).write_text("ran")']
    def test_occupied_port_never_launches_or_verifies(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));listener.listen();p=listener.getsockname()[1]
            cmd=self.command(p,['--server-argv',json.dumps([PY,'-c',f'from pathlib import Path;Path({str(self.root/"launched")!r}).write_text("ran")'])])
            result=run(cmd,expected=1)
        self.assertIn('PORT_IN_USE',result.stderr);self.assertFalse((self.root/'launched').exists());self.assertFalse((self.root/'verified').exists())
    def serve(self,p):
        script=self.root/'server.py';write(script,('from http.server import HTTPServer,BaseHTTPRequestHandler\n'
            'class H(BaseHTTPRequestHandler):\n'
            ' def do_GET(self):\n'
            '  self.send_response(200);self.end_headers();self.wfile.write(b\'{"revision":"fixture-revision"}\')\n'
            ' def log_message(self,*args):pass\n'
            f'HTTPServer(("127.0.0.1",{p}),H).serve_forever()\n').encode())
        return ['--server-argv',json.dumps([PY,str(script)]),'--timeout','4','--identity-path','/build-info.json','--identity-key','revision']
    def test_matching_local_identity_runs_verification_and_stops_server(self):
        p=port();args=self.serve(p)+['--identity-value','fixture-revision'];result=run(self.command(p,args))
        self.assertIn('declared JSON identity matched',result.stdout);self.assertTrue((self.root/'verified').exists());self.assertFalse(ws.port_open('127.0.0.1',p))
    def test_wrong_identity_never_runs_verification(self):
        p=port();args=self.serve(p)+['--identity-value','wrong'];args[args.index('4')]='1.0';result=run(self.command(p,args),expected=1)
        self.assertIn('SERVER_IDENTITY_MISMATCH',result.stderr);self.assertFalse((self.root/'verified').exists());self.assertFalse(ws.port_open('127.0.0.1',p))
    def test_external_identity_url_rejected(self):
        p=port();args=self.serve(p)+['--identity-value','x'];args[args.index('/build-info.json')]='//example.invalid/probe'
        run(self.command(p,args),expected=2);self.assertFalse((self.root/'verified').exists())
    def test_partial_identity_contract_rejected(self):
        run(self.command(port(),['--server-argv',json.dumps([PY,'-c','pass']),'--identity-path','/health']),expected=2)
    def test_launcher_exits_before_readiness(self):
        p=port();result=run(self.command(p,['--server-argv',json.dumps([PY,'-c','pass']),'--timeout','4']),expected=1)
        self.assertIn('SERVER_EXITED',result.stderr);self.assertFalse((self.root/'verified').exists())


class ExactRevisionTests(unittest.TestCase):
    def test_revision_identity_rejects_empty_prefix_and_overlong(self):
        from accept_release import revision_matches
        for bad in ('', 'a'*7, 'a'*39, 'a'*40+'b', 'not-a-sha',None):
            with self.subTest(bad=bad): self.assertFalse(revision_matches('a'*40,bad))
    def test_full_git_identity_only_case_insensitive(self):
        from accept_release import revision_matches
        self.assertTrue(revision_matches('a'*40,'A'*40))
        self.assertTrue(revision_matches('a'*64,'A'*64))
        self.assertFalse(revision_matches('a'*40,'b'*40))
    def test_observed_marker_is_full_token_not_short_or_embedded(self):
        from accept_release import observed_revision_marker
        expected='a'*40
        self.assertTrue(observed_revision_marker(expected,'{"revision":"'+expected+'"}'))
        for value in ('a'*7,expected+'b','b'+expected,'', 'b'*40):
            self.assertFalse(observed_revision_marker(expected,value))


class Identity(unittest.TestCase):
    def test_current_package_identity_bindings(self):
        import verify_package as vp
        self.assertEqual(vp.EXPECTED_VERSION,c.harness_version(ROOT))
        readme=ROOT/'README.md' if IS_SOURCE else ROOT/'.ai/harness/README.md'
        self.assertEqual(readme.read_text().splitlines()[0],'# Codex Product Harness v'+c.harness_version(ROOT))
        self.assertIn('## 5.5.7',(readme.parent/'CHANGELOG.md').read_text())
    def test_current_lineage_and_unchanged_parent_archive_record(self):
        doc=json.loads((ROOT/'.ai/lineage/v5.5.7.json').read_text());self.assertEqual(doc['distribution_version'],'5.5.7');self.assertEqual(doc['implementation_parent'],'5.5.6')
        prior=doc['prior_lineage'];self.assertEqual(hashlib.sha256((ROOT/prior['path']).read_bytes()).hexdigest(),prior['sha256'])
        self.assertEqual(next(x for x in doc['input_artifacts'] if x['role']=='implementation-parent')['sha256'],'f470013849aea59b3b4709849343b8d3555c8ae188df1d47035903ca5f43f0ab')
    def test_canonical_13_skills_remain_raw_byte_identical(self):
        expected=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text())['sha256'];self.assertEqual(len(expected),13)
        for name,value in expected.items():self.assertEqual(hashlib.sha256((ROOT/'.agents/skills'/name/'SKILL.md').read_bytes()).hexdigest(),value)

if __name__=='__main__':unittest.main(verbosity=2)

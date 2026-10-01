#!/usr/bin/env python3
"""v5.5.5: production parsers and copy-boundary regressions, not a Windows emulator."""
from __future__ import annotations
import contextlib, gc, hashlib, io, json, os, shutil, subprocess, sys, tempfile, unittest, warnings
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
import _common as c
import deterministic_regression_gate as gate
import skill_security_gate as sg

class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v555-');self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
    def source(self):
        root=self.p/'source';(root/'.ai/scripts').mkdir(parents=True)
        c.dump_json(root/'.ai/SOURCE_DISTRIBUTION.json',{'kind':'codex-product-harness-source-distribution'})
        c.dump_json(root/'.ai/DETERMINISTIC_E2E_POLICY.json',{'discovery_globs':['.ai/scripts/*_regression_test.py'],'exclude':[]})
        (root/'VERSION').write_bytes(b'fixture\n');return root

class FrontmatterTests(unittest.TestCase):
    clean='---\nname: clean\ndescription: bounded fixture\n---\nBody\n'
    def test_lf_and_crlf_same_semantics(self):
        self.assertEqual(sg.parse_frontmatter(self.clean),sg.parse_frontmatter(self.clean.replace('\n','\r\n')))
    def test_utf8_bom_before_delimiter_is_accepted(self):
        self.assertEqual(sg.parse_frontmatter(self.clean),sg.parse_frontmatter('\ufeff'+self.clean.replace('\n','\r\n')))
    def test_inline_separator_not_a_metadata_terminator(self):
        self.assertEqual(sg.parse_frontmatter('---\nname: clean---\ndescription: x\n'),{})
    def test_missing_metadata_still_reviewed(self):
        findings=[];sg.skill_specific('SKILL.md','Body only',findings)
        self.assertIn('skill-frontmatter',[f['rule'] for f in findings])
    def test_duplicate_metadata_not_clean(self):
        self.assertEqual(sg.parse_frontmatter('---\nname: a\nname: b\ndescription: x\n---\n'),{})
    def test_leading_prose_does_not_gain_metadata(self):
        self.assertEqual(sg.parse_frontmatter('text\n'+self.clean),{})

class FrontmatterIntegration(TempCase):
    def test_crlf_clean_skill_pass_and_raw_bytes_preserved(self):
        p=self.p/'SKILL.md';raw=FrontmatterTests.clean.replace('\n','\r\n').encode();p.write_bytes(raw)
        cp=subprocess.run([sys.executable,str(ROOT/'.ai/scripts/skill_security_gate.py'),'--target',str(self.p),'--fail-on','review'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr);self.assertEqual(json.loads(cp.stdout)['status'],'pass');self.assertEqual(p.read_bytes(),raw)
    def test_bom_crlf_raw_hash_not_normalized(self):
        p=self.p/'SKILL.md';raw=b'\xef\xbb\xbf'+FrontmatterTests.clean.replace('\n','\r\n').encode();p.write_bytes(raw)
        self.assertTrue(sg.parse_frontmatter(raw.decode('utf-8')));self.assertEqual(c._hash_file_content(p),hashlib.sha256(raw).hexdigest())

class GitParsingTests(TempCase):
    def test_stderr_never_becomes_machine_data(self):
        stderr=io.StringIO()
        with contextlib.redirect_stderr(stderr):
            rc,out=c.run_capture([sys.executable,'-c','import sys;sys.stderr.write("warning: LF to CRLF\\n");sys.stdout.write("real.txt\\0")'],self.p)
        self.assertEqual(rc,0);self.assertEqual(c.nul_paths(out),['real.txt']);self.assertIn('warning:',stderr.getvalue())
    def test_full_capture_keeps_failure_diagnostics(self):
        rc,out,err=c.run_capture_full([sys.executable,'-c','import sys;sys.stderr.write("denied");sys.exit(7)'],self.p)
        self.assertEqual((rc,out,err),(7,'','denied'))
    def test_paths_preserve_whitespace_unicode_and_newline(self):
        names=[' space .txt','a\nb.txt','t\tab.txt','\u0111\u1ed3.txt','warning: not a diagnostic']
        self.assertEqual(c.nul_paths('\0'.join(names)+'\0'),names)
    def test_rename_accounts_for_both_paths(self):
        self.assertEqual(c.parse_git_status_z('R  .ai/checkpoints/new\0product.txt\0'),[('R ','.ai/checkpoints/new'),('R ','product.txt')])
    def test_status_preserves_quoted_looking_name(self):
        self.assertEqual(c.parse_git_status_z('?? "quoted".txt\0'),[('??','"quoted".txt')])
    def test_truncated_status_rejected(self):
        with self.assertRaises(ValueError):c.parse_git_status_z('?? x')
    def test_incomplete_rename_rejected(self):
        with self.assertRaises(ValueError):c.parse_git_status_z('R  x\0')
    def test_failed_status_is_not_clean(self):
        with patch.object(c,'run_capture',return_value=(128,'')):
            with self.assertRaises(RuntimeError):c.git_status_entries(self.p)
    def test_failed_ls_files_is_not_empty_fingerprint(self):
        with patch.object(c,'git_info',return_value={'is_git':True}),patch.object(c,'run_capture',return_value=(128,'')):
            with self.assertRaises(RuntimeError):c.product_source_manifest(self.p)
    def test_real_git_special_filenames_and_runtime_exclusion(self):
        if not shutil.which('git'):self.skipTest('Git unavailable')
        subprocess.run(['git','init','-q',str(self.p)],check=True,capture_output=True)
        names=[' spaced .txt','\u0111\u1ed3.txt']
        if os.name!='nt':names+=['line\nbreak.txt','tab\tname.txt','"quoted".txt']
        for name in names:(self.p/name).write_bytes(b'value\r\n')
        (self.p/'.ai/checkpoints').mkdir(parents=True);(self.p/'.ai/checkpoints/state.json').write_bytes(b'{}')
        (self.p/'.ai/REPO_MAP.json').write_bytes(b'{}')
        env=os.environ.copy();env.update({'GIT_AUTHOR_NAME':'Fixture','GIT_AUTHOR_EMAIL':'fixture@example.invalid','GIT_COMMITTER_NAME':'Fixture','GIT_COMMITTER_EMAIL':'fixture@example.invalid'})
        subprocess.run(['git','-c','core.autocrlf=true','-c','core.safecrlf=warn','add','.'],cwd=self.p,check=True,capture_output=True,env=env)
        subprocess.run(['git','-c','commit.gpgsign=false','commit','-qm','fixture'],cwd=self.p,check=True,capture_output=True,env=env)
        m=c.product_source_manifest(self.p);self.assertEqual(set(m),set(names))
        for name in names:self.assertEqual(m[name],hashlib.sha256(b'value\r\n').hexdigest())

class TempBoundaryTests(TempCase):
    def test_explicit_descendant_rejected_before_creation(self):
        root=self.source();dest=root/'unsafe'
        with self.assertRaisesRegex(RuntimeError,'COPY_TEMP_OVERLAP'):c.safe_temp_base(root,str(dest),for_copy=True)
        self.assertFalse(dest.exists())
    def test_explicit_source_itself_rejected(self):
        root=self.source()
        with self.assertRaises(RuntimeError):c.safe_temp_base(root,str(root),for_copy=True)
    def test_external_sibling_allowed(self):
        root=self.source();scratch=self.p/'scratch';self.assertEqual(c.safe_temp_base(root,str(scratch),for_copy=True),scratch)
    def test_runtime_temp_inside_workspace_still_supported(self):
        root=self.source();dest=root/'.ai/checkpoints/tmp';self.assertEqual(c.safe_temp_base(root,str(dest)),dest)
    def test_denied_all_candidates_fails_without_unsafe_probe(self):
        root=self.source();visited=[]
        def denied(p):visited.append(p);return False
        with patch.object(c,'_writable_probe',side_effect=denied):
            with self.assertRaisesRegex(RuntimeError,'copy-safe'):c.safe_temp_base(root,for_copy=True)
        self.assertTrue(all(not p.is_relative_to(root) for p in visited))
    def test_harness_temp_dir_retains_precedence(self):
        root=self.source();first=self.p/'preferred';second=self.p/'legacy'
        with patch.dict(os.environ,{'HARNESS_TEMP_DIR':str(first),'HARNESS_TMP':str(second)}):
            self.assertEqual(c.safe_temp_base(root),first)
    def test_legacy_override_without_higher_priority_selector(self):
        root=self.source();second=self.p/'legacy'
        env=dict(os.environ);env.pop('HARNESS_TEMP_DIR',None);env['HARNESS_TMP']=str(second)
        with patch.dict(os.environ,env,clear=True):self.assertEqual(c.safe_temp_base(root),second)
    def test_nested_copy_rejected_without_creating_destination(self):
        root=self.source();dest=root/'child'
        with self.assertRaises(ValueError):c.copy_source_tree(root,dest)
        self.assertFalse(dest.exists())
    def test_ancestor_copy_rejected(self):
        root=self.source()
        with self.assertRaises(ValueError):c.copy_source_tree(root,self.p)
    def test_small_source_copy_outside_tree(self):
        root=self.source();dest=self.p/'clone';c.copy_source_tree(root,dest)
        self.assertEqual((dest/'VERSION').read_bytes(),b'fixture\n')
    def test_alias_into_source_rejected(self):
        root=self.source();link=self.p/'alias'
        try:link.symlink_to(root,target_is_directory=True)
        except OSError:self.skipTest('symlink privileges unavailable; not proof of junction behavior')
        with self.assertRaises(RuntimeError):c.safe_temp_base(root,str(link/'scratch'),for_copy=True)
        with self.assertRaises(ValueError):c.copy_source_tree(root,link/'clone')
        self.assertFalse((root/'scratch').exists())

class GateTests(TempCase):
    def installed(self):
        root=self.source();(root/'.ai/SOURCE_DISTRIBUTION.json').unlink()
        c.dump_json(root/'.ai/HARNESS_INSTALL_STATE.json',{'schema_version':2,'harness_version':'5.5.5'})
        (root/'.ai/harness').mkdir();(root/'.ai/harness/VERSION').write_bytes(b'5.5.5\n')
        (root/'VERSION').write_bytes(b'PRODUCT-99\n');return root
    def test_installed_version_uses_namespace(self):
        root=self.installed();r=gate.run_gate(root,False)
        self.assertEqual(r['runner_provenance']['harness_version'],'5.5.5');self.assertEqual(r['status'],'NOT_RUN')
    def test_installed_mode_stops_before_tests(self):
        root=self.installed();(root/'.ai/scripts/no_regression_test.py').write_text('raise AssertionError("must not execute")\n')
        with patch.object(gate,'_run_stream',side_effect=AssertionError('executed')):r=gate.run_gate(root)
        self.assertEqual(r['status'],'BLOCKED');self.assertEqual(r['reason_code'],'SOURCE_ONLY_REGRESSION_SUITE');self.assertEqual(r['tests'],[])
    def test_unsafe_temp_is_preflight_blocked(self):
        root=self.source();r=gate.run_gate(root,True,str(root/'nested'))
        self.assertEqual(r['status'],'BLOCKED');self.assertFalse((root/'nested').exists())
    def test_child_temp_outside_source_no_global_env_mutation(self):
        root=self.source();(root/'.ai/scripts/env_regression_test.py').write_text('import os,tempfile,pathlib\nr=pathlib.Path.cwd().resolve(); t=pathlib.Path(tempfile.gettempdir()).resolve()\nassert not t.is_relative_to(r)\nassert all(os.environ[k]==str(t) for k in ("TEMP","TMP","TMPDIR","HARNESS_TEMP_DIR","HARNESS_TMP"))\n')
        before=dict(os.environ);r=gate.run_gate(root,True,str(self.p/'scratch'))
        self.assertEqual(r['status'],'PASS',r);self.assertEqual(dict(os.environ),before)
    def test_capture_releases_pipe_without_resource_warning(self):
        root=self.source();(root/'.ai/scripts/pipe_regression_test.py').write_text('print("pipe fixture")\n')
        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter('always',ResourceWarning)
            result=gate.run_gate(root,True,str(self.p/'scratch'))
            gc.collect()
        self.assertEqual(result['status'],'PASS')
        self.assertFalse([str(w.message) for w in emitted if issubclass(w.category,ResourceWarning)])
    def test_timeout_not_pass(self):
        root=self.source();(root/'.ai/scripts/slow_regression_test.py').write_text('import time\ntime.sleep(30)\n')
        r=gate.run_gate(root,True,str(self.p/'scratch'),1)
        self.assertEqual(r['status'],'FAIL');self.assertEqual(r['tests'][0]['status'],'INFRA_ERROR');self.assertTrue(r['tests'][0]['timed_out'])
    def test_skip_not_counted_as_pass(self):
        r=gate._unittest_summary('Ran 7 tests in 1.0s\n\nOK (skipped=2)\n')
        self.assertEqual((r['passed'],r['skipped']),(5,2))
    def test_absent_unittest_summary_is_unknown(self):
        self.assertFalse(gate._unittest_summary('MY RUNNER: PASS')['known'])
    def test_wsl_provenance_is_not_native_windows(self):
        with patch.object(gate.platform,'release',return_value='6.6-microsoft-standard-WSL2'),patch.object(gate.platform,'system',return_value='Linux'),patch.object(gate.sys,'platform','linux'):
            r=gate.runtime_environment()
        self.assertEqual(r['kind'],'wsl-linux');self.assertFalse(r['is_native_windows_runtime'])

class PreservationTests(unittest.TestCase):
    def test_exact_parent_lineage(self):
        # Historical identity assertions continue against the exact archived parent bytes.
        lineage=json.loads((ROOT/'.ai/lineage/v5.5.5.json').read_text())
        self.assertEqual(lineage['distribution_version'],'5.5.5')
        self.assertEqual(lineage['canonical_baseline'],'5.3.0')
        self.assertEqual(lineage['implementation_parent'],'5.5.4')
        parents=[item for item in lineage['input_artifacts'] if item['role']=='implementation-parent']
        self.assertEqual(parents,[{'name':'Codex_Product_Harness_v5.5.4.zip','sha256':'fdbaf29e365d0bafc3d3e56e4dca0fc3c50babf449c7726873cdcbf4fc17553c','role':'implementation-parent'}])
    def test_13_skills_byte_identical(self):
        expected=json.loads((ROOT/'.ai/CANONICAL_SKILL_HASHES.json').read_text())['sha256'];self.assertEqual(len(expected),13)
        for name,digest in expected.items():self.assertEqual(c._hash_file_content(ROOT/'.agents/skills'/name/'SKILL.md'),digest)
    def test_quality_profiles_and_live_gate_preserved(self):
        q=json.loads((ROOT/'.ai/QUALITY.json').read_text());self.assertEqual(q['profile_required_checks']['native'],[])
        self.assertIn('verified-progress',q['profile_required_checks']['portable']);self.assertIn('verified-progress',q['profile_required_checks']['audited']);self.assertIn('skill-eval-live',q['trait_required_checks']['skill_modification'])

if __name__=='__main__':unittest.main(verbosity=2)

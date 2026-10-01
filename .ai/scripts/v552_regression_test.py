#!/usr/bin/env python3
"""Truth hardening regressions. All synthetic runs are fixtures, NOT live evals.
Every mutation is in an OS temporary directory; shipped files stay byte-identical.
"""
from __future__ import annotations
import concurrent.futures,copy,hashlib,json,os,shutil,sqlite3,subprocess,sys,tempfile,time,unittest,uuid
from pathlib import Path
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
ROOT=Path(__file__).resolve().parents[2]
from _truth import digest,inventory,parse_json,portable_rel,read_json,sha,write_json
from skill_trigger_eval import classify,bounded_run,run_case,validate_row
import skill_eval_transaction as tx
import operator_events as ledger
from validate_agent_plugin import validate as validate_plugin,SCHEMA
from export_agent_plugin import make_lock,safe_tree
from skill_eval_acceptance import causal_integrity,command_binding,validate_binding
from runtime_control_state import validate as validate_runtime
from mcp_client_regression import ResponseGuard,run_suite
from _common import product_source_digest


def stream(*blocks):
    replies=[{'type':'tool_result','tool_use_id':eid,'content':'fixture Skill loaded','is_error':False} for eid in dict.fromkeys(b['id'] for b in blocks if b.get('type')=='tool_use' and b.get('name')=='Skill')]
    events=[{'type':'assistant','message':{'role':'assistant','content':list(blocks)}}, {'type':'user','message':{'role':'user','content':replies}}, {'type':'result','is_error':False}]
    return b''.join(json.dumps(x).encode()+b'\n' for x in events)

def tool(name='Skill',skill='alpha',eid='native-tool-1'):
    return {'type':'tool_use','name':name,'id':eid,'input':{'skill':skill}}

def capture(raw,**changes):
    cap={'returncode':0,'timed_out':False,'overflow':False,'stream_closed':True,
         'trace_sha256':hashlib.sha256(raw).hexdigest(),'capture_format':'claude-stream-json',
         'invocation_mode':'autonomous','evidence_tier':'fixture','approved_adapter_sha256':'a'*64}
    cap.update(changes);return cap

class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cph-v552-');self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
    def skills(self):
        p=self.p/'skills';p.mkdir()
        for name in ('alpha','beta'):
            (p/name).mkdir();(p/name/'SKILL.md').write_text('---\nname: '+name+'\ndescription: Sample fixture only.\n---\nInstruction\n')
        return p

class TriggerTests(TempCase):
    def test_full_trace_after_bash(self):
        raw=stream(tool('Bash',eid='bash'),tool());r=classify(raw,capture(raw),'alpha')
        self.assertEqual(r['state'],'TRIGGERED');self.assertEqual(r['activation_event_ids'],['native-tool-1']);self.assertFalse(r['live_eligible'])
    def test_negative_complete_stream(self):
        raw=stream();self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'NOT_TRIGGERED')
    def test_self_report_and_read_do_not_prove_activation(self):
        for block in ({'type':'text','text':'I activated Skill alpha'},tool('Read'),{'type':'tool_result','content':'Skill alpha'}):
            with self.subTest(block=block):
                raw=stream(block);self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'NOT_TRIGGERED')
    def test_identity_is_exact(self):
        for name in ('beta','x:alpha','alpha-clone','Alpha'):
            with self.subTest(name=name):
                raw=stream(tool(skill=name));self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'NOT_TRIGGERED')
    def test_forced_invocation_uncertain(self):
        raw=stream(tool());self.assertEqual(classify(raw,capture(raw,invocation_mode='user-slash'),'alpha')['state'],'ATTRIBUTION_UNCERTAIN')
    def test_unknown_hosts_never_borrow_native_semantics(self):
        raw=stream(tool())
        for fmt in ('codex-unverified','antigravity-unverified','gemini-unverified'):
            self.assertEqual(classify(raw,capture(raw,capture_format=fmt),'alpha')['state'],'ATTRIBUTION_UNCERTAIN')
    def test_infra_failure_never_negative_pass(self):
        raw=stream()
        for kw in ({'returncode':1},{'timed_out':True},{'overflow':True},{'stream_closed':False},{'trace_sha256':'0'*64}):
            with self.subTest(kw=kw): self.assertEqual(classify(raw,capture(raw,**kw),'alpha')['state'],'INFRA_ERROR')
    def test_partial_and_malformed_traces(self):
        for raw in (b'',b'{}\n',b'{"type":"result","is_error":true}\n',stream()+b'{}\n',b'{"type":"result","type":"assistant"}\n',b'[]\n',b'\xff'):
            with self.subTest(raw=raw):self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'INFRA_ERROR')
    def test_skill_request_without_completion_is_not_activation(self):
        events=[{'type':'assistant','message':{'role':'assistant','content':[tool()]}},{'type':'result','is_error':False}]
        raw=b''.join(json.dumps(e).encode()+b'\n' for e in events)
        self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'ATTRIBUTION_UNCERTAIN')
    def test_failed_skill_load_never_passes(self):
        raw=stream(tool()).replace(b'"is_error": false',b'"is_error": true',1)
        self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'INFRA_ERROR')
    def test_event_dedup_and_conflict(self):
        raw=stream(tool(),tool());self.assertEqual(len(classify(raw,capture(raw),'alpha')['activation_event_ids']),1)
        raw=stream(tool(),tool(skill='beta'));self.assertEqual(classify(raw,capture(raw),'alpha')['state'],'INFRA_ERROR')
    def test_bounded_timeout_and_output(self):
        for argv,timeout,limit in (([sys.executable,'-S','-c','import time; time.sleep(5)'],.1,10000),([sys.executable,'-S','-c','print("x"*100000)'],2,2048)):
            start=time.monotonic();raw,cap=bounded_run(argv,self.p,os.environ.copy(),timeout,limit)
            self.assertTrue(cap['timed_out'] or cap['overflow']);self.assertLess(time.monotonic()-start,4);self.assertLessEqual(len(raw),limit)
    def test_1_2_8_worker_isolation_and_fixture_rejection(self):
        skills=self.skills();case={'id':'c','skill':'alpha','prompt':'normal prompt with no activation hints'}
        # The fixture asserts exactly one native skill and a fresh HOME in each worker.
        code="import os,pathlib,json; p=pathlib.Path('.claude/skills'); assert [x.name for x in p.iterdir()]==['alpha']; h=pathlib.Path(os.environ['HOME']); assert not (h/'seen').exists(); (h/'seen').write_text('1'); print(json.dumps({'type':'assistant','message':{'role':'assistant','content':[{'type':'tool_use','name':'Skill','id':'e','input':{'skill':'alpha'}}]}})); print(json.dumps({'type':'user','message':{'role':'user','content':[{'type':'tool_result','tool_use_id':'e','content':'fixture loaded','is_error':False}]}})); print(json.dumps({'type':'result','is_error':False}))"
        spec={'argv':[sys.executable,'-S','-c',code],'capture_format':'claude-stream-json','timeout_seconds':5}
        nonces=[]
        for workers in (1,2,8):
            out=self.p/str(workers);out.mkdir()
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                rows=list(pool.map(lambda n:run_case(case,spec,skills,out,n,tier='fixture'),range(1,9)))
            self.assertEqual([r['state'] for r in rows],['TRIGGERED']*8)
            for row in rows:
                self.assertFalse(row['live_eligible']);nonces.append(row['capture_dir'])
                with self.assertRaises(ValueError):validate_row(row,out,case,skills)
        self.assertEqual(len(set(nonces)),24)
    def test_capture_tamper_and_drift(self):
        skills=self.skills();out=self.p/'runs';out.mkdir();case={'id':'c','skill':'alpha','prompt':'a sufficiently long neutral request'}
        spec={'argv':[sys.executable,'-S','-c',"print('{\"type\":\"result\",\"is_error\":false}')"],'capture_format':'claude-stream-json'}
        row=run_case(case,spec,skills,out,1,tier='fixture')
        (out/row['capture_dir']/'trace.jsonl').write_text('changed')
        with self.assertRaises(ValueError):validate_row(row,out,case,skills)
    def test_legacy_report_not_acceptance(self):
        from skill_eval import activation_report,matrix_and_policy
        matrix,policy=matrix_and_policy(ROOT);rows=[]
        for c in matrix['cases']:
            for n in (1,2):rows.append({'case_id':c['id'],'run':n,'telemetry':'trace','observed_skills':[c['skill']] if c['polarity']=='should_trigger' else []})
        p=self.p/'rows.jsonl';p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        result,code=activation_report(matrix,policy,p,ROOT,True)
        self.assertEqual(code,0);self.assertFalse(result['acceptance_eligible'])
        result,code=activation_report(matrix,policy,p,ROOT)
        self.assertNotEqual(code,0);self.assertEqual(len(result['rejected_rows']),len(rows))
    def test_live_gate_rejects_echo_legacy_and_missing_binding(self):
        with self.assertRaises(ValueError):command_binding(ROOT,[sys.executable,'-S','-c','print("PASS")'])
        with self.assertRaises(ValueError):command_binding(ROOT,[sys.executable,'.ai/scripts/skill_eval.py','report','--runs','x','--legacy-diagnostic','--fail-on-regression'])
        with self.assertRaises(ValueError):validate_binding(ROOT,None)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):parse_json('{"score":0,"score":1}')

class PluginTests(TempCase):
    def plugin(self):
        p=self.p/'plugin';p.mkdir();shutil.copytree(ROOT/'.agents/skills',p/'skills')
        write_json(p/'plugin.json',{'$schema':SCHEMA,'name':'fixture-skills','version':'5.5.2'})
        make_lock(p,'5.5.2');return p
    def test_valid_exact_13_skills(self):
        r=validate_plugin(self.plugin());self.assertEqual(r['errors'],[]);self.assertEqual(len(r['discovered_skills']),13);self.assertFalse(r['host_install_permission_sandbox_parity'])
    def test_unknown_manifest_field_blocks_authoring_only(self):
        p=self.plugin();d=read_json(p/'plugin.json');d['hooks']={};write_json(p/'plugin.json',d);make_lock(p,'5.5.2')
        self.assertTrue(validate_plugin(p)['errors'])
    def test_added_removed_changed_artifact(self):
        p=self.plugin();f=next((p/'skills').glob('*/SKILL.md'));original=f.read_bytes()
        f.write_bytes(original+b'\n');self.assertTrue(validate_plugin(p)['errors']);f.write_bytes(original)
        f.unlink();self.assertTrue(validate_plugin(p)['errors']);f.write_bytes(original)
        (p/'skills/extra.txt').write_text('extra');self.assertTrue(validate_plugin(p)['errors'])
    def test_nested_skill_rejected_without_losing_valid_discovery(self):
        p=self.plugin();x=p/'skills/nested/deeper';x.mkdir(parents=True);(x/'SKILL.md').write_text('---\nname: x\ndescription: x\n---\n');make_lock(p,'5.5.2')
        r=validate_plugin(p);self.assertTrue(r['errors']);self.assertEqual(len(r['discovered_skills']),13)
    def test_invalid_skill_has_independent_discovery_result(self):
        p=self.plugin();next((p/'skills').glob('*/SKILL.md')).write_text('no frontmatter');make_lock(p,'5.5.2')
        r=validate_plugin(p);self.assertTrue(r['errors']);self.assertEqual(len(r['discovered_skills']),12);self.assertEqual(len(r['skipped_skills']),1)
    def test_duplicate_or_traversal_lock_entry(self):
        p=self.plugin();d=read_json(p/'plugin-lock.json');d['files'].append(d['files'][0]);write_json(p/'plugin-lock.json',d)
        self.assertTrue(validate_plugin(p)['errors']);d['files'][-1]['path']='../escape';write_json(p/'plugin-lock.json',d)
        self.assertTrue(validate_plugin(p)['errors'])
    @unittest.skipIf(os.name=='nt','Unix symlink fixture; Windows junction has a separate test')
    def test_symlink_escape_rejected_before_copy(self):
        p=self.plugin();outside=self.p/'outside';outside.mkdir();(outside/'secret').write_text('sentinel')
        (p/'skills/link').symlink_to(outside,target_is_directory=True)
        self.assertTrue(validate_plugin(p)['errors']);self.assertTrue(safe_tree(p/'skills'));self.assertEqual((outside/'secret').read_text(),'sentinel')
    @unittest.skipIf(os.name=='nt','Unix symlink fixture')
    def test_internal_symlink_and_lock_symlink_rejected(self):
        p=self.plugin();(p/'skills/alias').symlink_to(next((p/'skills').iterdir()),target_is_directory=True)
        self.assertTrue(validate_plugin(p)['errors']);(p/'skills/alias').unlink()
        f=p/'plugin-lock.json';old=self.p/'saved-lock';shutil.move(f,old);f.symlink_to(old)
        self.assertTrue(validate_plugin(p)['errors'])
    @unittest.skipUnless(os.name=='nt','Windows junction runtime not available on this OS')
    def test_windows_junction_escape(self):
        p=self.plugin();outside=self.p/'outside';outside.mkdir()
        subprocess.run(['cmd','/c','mklink','/J',str(p/'skills/junction'),str(outside)],check=True,stdout=subprocess.PIPE)
        try:self.assertTrue(validate_plugin(p)['errors'])
        finally:os.rmdir(p/'skills/junction')
    def test_portable_path_rejections(self):
        for value in ('../x','a/../b','a\\b','C:/x','/x','a//b','CON.txt','nul','x.','x ','a:stream'):
            with self.subTest(value=value),self.assertRaises(ValueError):portable_rel(value)
    def test_export_refuses_existing_destination(self):
        out=self.p/'existing.zip';out.write_bytes(b'keep')
        p=subprocess.run([sys.executable,'-S',str(ROOT/'.ai/scripts/export_agent_plugin.py'),'--out',str(out)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        self.assertNotEqual(p.returncode,0);self.assertEqual(out.read_bytes(),b'keep')

class TransactionTests(TempCase):
    def setup_experiment(self):
        skills=self.skills();matrix={'cases':[{'id':'c','prompt':'a sufficiently long fixture prompt','split':'tune','skill':'alpha','polarity':'should_trigger'}]}
        runtime={'agent':'fixture','model':'fixture','reasoning_effort':'none','cli_version':'0','source_revision':'rev-a'}
        exp=self.p/'experiment';tx.prepare(exp,matrix,skills,runtime,2,graders={'c':{'kind':'text-predicate-v1','equals':'correct'}})
        return exp,skills,matrix,runtime
    def completed(self,exp,skills,name='run',variant='with_skill',rep=1):
        p=self.p/name;tx.start(exp,p,'c',rep,variant,skills if variant=='with_skill' else None)
        (p/'trace.jsonl').write_bytes(b'{"fixture":true}\n');(p/'output.txt').write_text('correct')
        write_json(p/'capture.json',{'process_complete':True,'provider_response_complete':True,'trace_complete':True,'returncode':0,'evidence_tier':'fixture','trace_sha256':sha(p/'trace.jsonl')})
        write_json(p/'metrics.json',{'input_tokens':2,'output_tokens':1,'duration_seconds':.1,'billing_class':'local'})
        write_json(p/'grade.json',tx.deterministic_grade(exp,p));return p
    def test_commit_pair_and_recommit(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);b=self.completed(e,s,'base','without_skill')
        tx.commit(e,a);tx.commit(e,b);self.assertEqual(tx.compare(e,a,b)['status'],'pair-integrity-pass')
        with self.assertRaises(ValueError):tx.commit(e,a)
    def test_partial_marker_missing(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s)
        with self.assertRaises((ValueError,OSError)):tx.verify(e,a)
    def test_required_trace_missing(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);(a/'trace.jsonl').unlink()
        with self.assertRaises(ValueError):tx.commit(e,a)
    def test_incomplete_process_provider_or_trace(self):
        e,s,_,_=self.setup_experiment()
        for key in ('process_complete','provider_response_complete','trace_complete'):
            a=self.completed(e,s,key);d=read_json(a/'capture.json');d[key]=False;write_json(a/'capture.json',d)
            with self.assertRaises(ValueError):tx.commit(e,a)
    def test_artifact_mutation_added_and_deleted(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);tx.commit(e,a)
        (a/'extra.txt').write_text('unexpected')
        with self.assertRaises(ValueError):tx.verify(e,a)
        (a/'extra.txt').unlink();(a/'output.txt').write_text('wrong')
        with self.assertRaises(ValueError):tx.verify(e,a)
        (a/'output.txt').unlink()
        with self.assertRaises(ValueError):tx.verify(e,a)
    def test_design_prompt_and_runtime_drift(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);tx.commit(e,a)
        d=read_json(e/'answer-design.json');d['runtime']['model']='another';write_json(e/'answer-design.json',d)
        with self.assertRaises(ValueError):tx.verify(e,a)
    def test_rehashed_design_still_invalidates_prior_run(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);tx.commit(e,a)
        d=read_json(e/'answer-design.json');d.pop('design_sha256');d['cases'][0]['prompt_sha256']='0'*64;d['design_sha256']=digest(d);write_json(e/'answer-design.json',d)
        with self.assertRaises(ValueError):tx.verify(e,a)
    def test_materialized_tree_and_without_arm(self):
        e,s,_,_=self.setup_experiment();(s/'alpha/SKILL.md').write_text('changed')
        with self.assertRaises(ValueError):tx.start(e,self.p/'bad','c',1,'with_skill',s)
        with self.assertRaises(ValueError):tx.start(e,self.p/'bad2','c',1,'without_skill',s)
    def test_same_arm_is_not_a_pair(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);b=self.completed(e,s,'other');tx.commit(e,a);tx.commit(e,b)
        with self.assertRaises(ValueError):tx.compare(e,a,b)
    def test_deterministic_grade_recomputed(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s);self.assertEqual(tx.deterministic_grade(e,a)['score'],1)
        (a/'output.txt').write_text('wrong');self.assertEqual(tx.deterministic_grade(e,a)['score'],0)
    def test_no_grader_means_no_causal_acceptance(self):
        e,s,_,_=self.setup_experiment();a=self.completed(e,s)
        d=read_json(e/'answer-design.json');d.pop('design_sha256');d['graders']={};d['design_sha256']=digest(d);write_json(e/'answer-design.json',d)
        with self.assertRaises(ValueError):tx.deterministic_grade(e,a)
    def test_fixture_commits_never_live_causal_proof(self):
        e,s,m,r=self.setup_experiment();a=self.completed(e,s);tx.commit(e,a)
        root=self.p/'root';(root/'.agents').mkdir(parents=True);shutil.copytree(s,root/'.agents/skills')
        row={'experiment_dir':'experiment','artifact_dir':'run','case_id':'c','run':1,'variant':'with_skill','runtime':r,'score':1,'metrics':read_json(a/'metrics.json')}
        errors=causal_integrity([row],self.p,m,root);self.assertTrue(any('not an approved live' in x for x in errors))
    def test_file_removal_ablation_provenance(self):
        s=self.skills();child=self.p/'ablation';shutil.copytree(s,child);(child/'beta/SKILL.md').unlink()
        result=tx.ablation_provenance(s,child,['beta/SKILL.md']);self.assertEqual(result['canonical_parent_sha256'],digest(inventory(s)))
        (child/'alpha/SKILL.md').write_text('changed')
        with self.assertRaises(ValueError):tx.ablation_provenance(s,child,['beta/SKILL.md'])
    def test_nonfinite_metrics_and_json(self):
        for text in ('{"n":NaN}','{"n":Infinity}'):
            with self.assertRaises(ValueError):parse_json(text)

class LedgerTests(TempCase):
    def db(self):return self.p/'.ai/checkpoints/operator-events.sqlite3'
    def test_absent_optional_runtime_remains_absent(self):
        self.assertEqual(validate_runtime(self.p)['status'],'pass');self.assertFalse((self.p/'.ai').exists())
    def test_enqueue_idempotent_and_payload_collision(self):
        p=self.db();ledger.enqueue(p,'instruction','e1');ledger.enqueue(p,'instruction','e1');self.assertEqual(ledger.status(p)['events'],1)
        with self.assertRaises(ValueError):ledger.enqueue(p,'different','e1')
    def test_fifo_claim_and_ack_not_progress(self):
        p=self.db();ledger.enqueue(p,'one','e1');ledger.enqueue(p,'two','e2');a=ledger.claim(p,'r1');self.assertEqual(a['event_id'],'e1')
        b=ledger.claim(p,'r1');self.assertEqual(a['token'],b['token'])
        r=ledger.acknowledge(p,'e1','r1',a['token'],'1'*64);self.assertFalse(r['verified_progress'])
        self.assertEqual(ledger.claim(p,'r2')['event_id'],'e2')
    def test_ambiguous_claim_blocks_new_round(self):
        p=self.db();ledger.enqueue(p,'one','e1');ledger.claim(p,'r1')
        with self.assertRaises(ValueError):ledger.claim(p,'r2')
    def test_digest_pinned_explicit_recovery(self):
        p=self.db();ledger.enqueue(p,'one','e1');a=ledger.claim(p,'r1')
        with self.assertRaises(ValueError):ledger.recover(p,'e1','0'*64,'replay','reason','operator')
        r=ledger.recover(p,'e1',a['claim_hash'],'replay','confirmed not applied','operator');self.assertFalse(r['external_side_effect_replay'])
        b=ledger.claim(p,'r2');self.assertNotEqual(a['token'],b['token'])
        with self.assertRaises(ValueError):ledger.acknowledge(p,'e1','r1',a['token'],'1'*64)
    def test_wrong_round_and_receipt(self):
        p=self.db();ledger.enqueue(p,'one','e1');a=ledger.claim(p,'r1')
        with self.assertRaises(ValueError):ledger.acknowledge(p,'e1','r2',a['token'],'1'*64)
        with self.assertRaises(ValueError):ledger.acknowledge(p,'e1','r1',a['token'],'fake')
    def test_concurrent_duplicate_enqueue(self):
        p=self.db();ledger.enqueue(p,'seed','seed')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _:ledger.enqueue(p,'same','dedup'),range(16)))
        self.assertEqual(ledger.status(p)['events'],2)
    def test_crash_after_claim_preserves_blocked_delivery(self):
        p=self.db();ledger.enqueue(p,'one','e1')
        code="import sys,os;sys.path.insert(0,sys.argv[1]);from pathlib import Path;from operator_events import claim;claim(Path(sys.argv[2]),'crashed-round');os._exit(17)"
        child=subprocess.run([sys.executable,'-S','-c',code,str(ROOT/'.ai/scripts'),str(p)]);self.assertEqual(child.returncode,17)
        with self.assertRaises(ValueError):ledger.claim(p,'new-round')
        self.assertTrue(ledger.claim(p,'crashed-round')['resumed_claim'])
    def test_chain_tamper_is_detected(self):
        p=self.db();ledger.enqueue(p,'one','e1')
        db=sqlite3.connect(p);db.execute("UPDATE events SET hash=?",('0'*64,));db.commit();db.close()
        self.assertEqual(validate_runtime(self.p)['status'],'fail')
    def test_future_schema_rejected(self):
        p=self.db();ledger.enqueue(p,'one','e1');db=sqlite3.connect(p);db.execute('PRAGMA user_version=99');db.close()
        with self.assertRaises(ValueError):ledger.enqueue(p,'two','e2')
    def test_runtime_exclusions_but_control_validation(self):
        (self.p/'app.txt').write_bytes(b'product\r\n');before=product_source_digest(self.p)
        ledger.enqueue(self.db(),'instruction','e1');write_json(self.p/'.ai/REPO_MAP.json',{'schema_version':1,'entries':[{'trust':'inferred','execution_enabled':False}]})
        self.assertEqual(product_source_digest(self.p),before);self.assertEqual(validate_runtime(self.p)['status'],'pass')
        write_json(self.p/'.ai/REPO_MAP.json',{'schema_version':1,'entries':[{'trust':'inferred','execution_enabled':True}]})
        self.assertEqual(product_source_digest(self.p),before);self.assertEqual(validate_runtime(self.p)['status'],'fail')
    def test_repo_map_unknown_trust_and_schema(self):
        for doc in ({'schema_version':2,'entries':[]},{'schema_version':1,'entries':[{'trust':'guessed'}]}):
            write_json(self.p/'.ai/REPO_MAP.json',doc);self.assertEqual(validate_runtime(self.p)['status'],'fail')
    def test_bounded_input(self):
        for text in ('','x'*16385):
            with self.assertRaises(ValueError):ledger.enqueue(self.db(),text,'e')

class MCPTests(TempCase):
    def test_ten_stdio_scenarios_and_scope(self):
        sent=self.p/'AGENTS.md';sent.write_bytes(b'project-owned\r\n');r=run_suite()
        self.assertEqual(r['status'],'pass');self.assertEqual(len(r['cases']),10)
        self.assertEqual(r['real_host_abuse_verification'],'UNVERIFIED');self.assertEqual(r['model_tokens'],0);self.assertEqual(sent.read_bytes(),b'project-owned\r\n')
    def test_circuit_stays_open(self):
        g=ResponseGuard('server')
        with self.assertRaises(ValueError):g.accept(b'bad')
        with self.assertRaises(ValueError):g.accept(b'{"jsonrpc":"2.0","id":1,"result":{"tools":[]}}')
    def test_server_namespace_is_part_of_identity(self):
        raw=b'{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"lookup"}]}}'
        a=ResponseGuard('a');b=ResponseGuard('b');a.accept(raw);b.accept(raw)
        self.assertNotEqual(a.tool_ids,b.tool_ids)

class PolicyTests(TempCase):
    def test_traits_preserve_baseline_and_all_profiles(self):
        q=read_json(ROOT/'.ai/QUALITY.json');checks=q['trait_required_checks']['harness_modification']
        for c in ('harness-security','surface-drift','package-contract','harness-self-test','skill-eval-contract','skill-trigger-truth-contract','skill-eval-transaction-contract','plugin-containment-contract','operator-event-contract','mcp-client-abuse-contract'):
            self.assertIn(c,checks)
        self.assertIn('skill-eval-live',q['trait_required_checks']['skill_modification'])
        self.assertIn('verified-progress',q['profile_required_checks']['portable']);self.assertIn('verified-progress',q['profile_required_checks']['audited'])
    @unittest.skipUnless((ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file(),'source-only installer regression; tested on source release')
    def test_newer_install_blocked_before_mutation(self):
        from install_plan import build_plan
        version=self.p/'.ai/harness/VERSION';version.parent.mkdir(parents=True);version.write_bytes(b'5.6.0\r\n')
        with self.assertRaisesRegex(ValueError,'newer installed'):build_plan(ROOT,self.p)
        self.assertEqual(version.read_bytes(),b'5.6.0\r\n')
    @unittest.skipUnless((ROOT/'.ai/SOURCE_DISTRIBUTION.json').is_file(),'source-only installer regression; tested on source release')
    def test_foreign_topology_requires_migration(self):
        from install_plan import build_plan
        (self.p/'.agents/skills/codex-product-harness/.ai').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'foreign'):build_plan(ROOT,self.p)


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--report');a=ap.parse_args()
    started=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]);result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'pass' if result.wasSuccessful() else 'fail','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':[{'test':str(t),'reason':why} for t,why in result.skipped],
            'duration_seconds':round(time.monotonic()-started,4),'platform':sys.platform,'python':sys.version.split()[0],
            'scope':'deterministic-and-local-subprocess-regression','live_skill_activation':'NOT_RUN','real_host_mcp_abuse':'NOT_RUN','fixture_runs_are_live_evidence':False}
    if a.report:write_json(Path(a.report),report)
    print('V5.5.2 REGRESSION: '+json.dumps(report,sort_keys=True));raise SystemExit(not result.wasSuccessful())
if __name__=='__main__':main()

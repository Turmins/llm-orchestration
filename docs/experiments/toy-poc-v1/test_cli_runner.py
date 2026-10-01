"""Synthetic parser/controller checks. No Codex processes or model requests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cli_runner as r
import harness


def fixture(answer='42', usage=None):
    # Counters supplied by user smoke report, wrapped in SYNTHETIC events.
    # This is NOT the original Windows JSONL and not a reproduced live run.
    if usage is None:
        usage=dict(input_tokens=15445,cached_input_tokens=12032,cache_write_input_tokens=0,
                   output_tokens=5,reasoning_output_tokens=0)
    return [dict(type='thread.started',thread_id='SYNTHETIC-thread'),dict(type='turn.started'),
            dict(type='item.completed',item=dict(id='SYNTHETIC-answer',type='agent_message',text=answer)),
            dict(type='turn.completed',usage=usage)]


def encode(events):
    return ('\n'.join(json.dumps(e,ensure_ascii=False) for e in events)+'\n').encode('utf-8')


def row(ident='SYNTHETIC-stage', policies=None):
    return dict(stage_id=ident,logical_strategies=policies or ['W-only','W-to-E'],
                telemetry=r.parse_events(encode(fixture()),0))


class CliTests(unittest.TestCase):
    def test_reported_counters_no_double_count(self):
        t=r.totals([row()])
        self.assertEqual(t['input_plus_output'],15450)
        self.assertEqual(t['cached_input_tokens'],12032)
        self.assertEqual(t['cache_write_input_tokens'],0)
        self.assertIsNone(t['api_charge'])
        self.assertIsNone(row()['telemetry']['actual_model'])

    def test_utf8_and_bom(self):
        data=b'\xef\xbb\xbf'+encode(fixture('{"text":"Привет — 東京"}'))
        p=r.parse_events(data,0)
        self.assertTrue(p['valid'])
        self.assertIn('東京',p['answer'])

    def test_optional_counters_null(self):
        p=r.parse_events(encode(fixture(usage={'input_tokens':10,'output_tokens':3})),0)
        self.assertTrue(p['valid'])
        self.assertIsNone(p['usage']['cached_input_tokens'])
        self.assertIsNone(p['usage']['cache_write_input_tokens'])

    def test_missing_required_and_invalid_counters(self):
        for usage in ({'input_tokens':10}, {'input_tokens':True,'output_tokens':3},
                      {'input_tokens':0,'output_tokens':0}, {'input_tokens':-1,'output_tokens':3},
                      {'input_tokens':10,'output_tokens':3,'reasoning_output_tokens':4}):
            self.assertFalse(r.parse_events(encode(fixture(usage=usage)),0)['valid'])

    def test_failure_and_partial_not_success(self):
        for code,timeout in [(1,False),(0,True),(None,False)]:
            p=r.parse_events(encode(fixture()),code,timeout)
            self.assertFalse(p['valid'])
            self.assertEqual(p['usage']['input_tokens'],15445)
        x=row();x['telemetry']['valid']=False
        t=r.totals([x]);self.assertIsNone(t['input_tokens'])
        self.assertEqual(t['input_tokens_known_subtotal'],15445)
        self.assertIsNone(t['input_plus_output'])
        self.assertFalse(r.parse_events(b'',1)['valid'])

    def test_duplicate_turn_and_json_keys_rejected(self):
        e=fixture();e.append(e[-1]);self.assertFalse(r.parse_events(encode(e),0)['valid'])
        self.assertFalse(r.parse_events(b'{"type":"turn.started","type":"turn.completed"}\n',0)['valid'])
        for s in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):r.strict_json(s)

    def test_tool_and_reroute_stop(self):
        for kind in ('command_execution','mcp_tool_call','collab_tool_call','web_search','file_change','new_unknown_tool'):
            e=fixture();e.insert(2,dict(type='item.started',item=dict(type=kind)))
            self.assertFalse(r.parse_events(encode(e),0)['valid'])
        e=fixture();e.insert(2,dict(type='item.completed',item=dict(type='error',message='model rerouted: a -> b (reason)')))
        p=r.parse_events(encode(e),0)
        self.assertFalse(p['valid']);self.assertTrue(p['rerouted']);self.assertIsNone(p['actual_model'])

    def test_shared_physical_and_logical(self):
        w=row();e=row('SYNTHETIC-E',['E-only']);take=row('SYNTHETIC-take',['W-to-E'])
        rows=[w,e,take]
        self.assertEqual(r.totals(rows)['stages'],3)
        self.assertEqual(r.totals([w,w])['stages'],1)
        self.assertEqual(r.totals([x for x in rows if 'W-only' in x['logical_strategies']])['input_tokens'],15445)
        self.assertEqual(r.totals([x for x in rows if 'W-to-E' in x['logical_strategies']])['input_tokens'],30890)
        bad=copy.deepcopy(w);bad['telemetry']['usage']['input_tokens']+=1
        with self.assertRaises(ValueError):r.totals([w,bad])

    def test_hidden_failure_does_not_route(self):
        calls=[]
        def call(task,role,stage,logical,parent=None):
            calls.append((task,role,stage))
            # Deliberately suboptimal but visibly valid P03; no hidden result enters runner.
            c={'path':['S','T'],'cost':9} if task=='P03' and role=='W' else harness.reference(task)
            return dict(candidate=c,stage_id='SYNTHETIC-'+task+role)
        with patch.object(harness,'grade',side_effect=AssertionError('hidden grader called during routing')):
            chosen=r.comparison(call)
        self.assertEqual(len(calls),8)
        self.assertIs(chosen['P03']['W-only'],chosen['P03']['W-to-E'])
        self.assertFalse(harness.grade('P03',chosen['P03']['W-only']['candidate']))
        self.assertEqual(calls[:4],[('P01','W','initial'),('P01','E','initial'),('P02','E','initial'),('P02','W','initial')])

    def test_visible_failure_one_takeover(self):
        calls=[]
        def call(task,role,stage,logical,parent=None):
            calls.append((task,role,stage))
            return dict(candidate=None if role=='W' else harness.reference(task),stage_id='SYNTHETIC-'+task+role)
        chosen=r.comparison(call)
        self.assertEqual(len(calls),12)
        self.assertEqual(sum(stage=='takeover' for _,_,stage in calls),4)
        self.assertEqual(len(chosen),4)

    def test_packet_and_controller_separation(self):
        for task in harness.TASKS:
            p=harness.packet(task)
            self.assertEqual(set(p),{'task_id','instruction','input','visible_rule','response_format'})
            self.assertNotIn('reference',p)
        args=r.base_args('codex.exe',r.DISABLE)
        self.assertIn('forced_login_method="chatgpt"',args)
        self.assertIn('read-only',args)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',args)
        self.assertNotIn('resume',args)

    def test_freeze_before_acceptance_and_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);stage=path/'SYNTHETIC-stage';stage.mkdir()
            content=b'{"path":["S","T"],"cost":9}'
            (stage/'candidate.txt').write_bytes(content)
            x=row();x.update(candidate_sha256=r.sha(content),candidate=r.strict_json(content))
            s=r.finish(path,[x],{'P03':{'W-only':x}},None,False)
            self.assertFalse(s['acceptance']['P03']['W-only']['independently_computed_acceptance'])
            self.assertTrue((path/'frozen-candidates.json').exists())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);stage=path/'SYNTHETIC-stage';stage.mkdir();(stage/'candidate.txt').write_bytes(b'changed')
            with self.assertRaises(ValueError):r.finish(path,[x],{},None,False)

    def test_binary_stdin_capture_and_nonzero_status(self):
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            # Explicitly SYNTHETIC local subprocess, never codex or inference.
            script="import sys; b=sys.stdin.buffer.read(); sys.stdout.buffer.write(b); sys.stderr.buffer.write(b'SYNTHETIC stderr'); sys.exit(7)"
            body='{"synthetic":"Привет — 東京"}\n'.encode('utf-8')
            result,out,err=r.capture([sys.executable,'-c',script],root,root/'capture',body)
            self.assertEqual(result['exit_code'],7)
            self.assertEqual(out,body)
            self.assertEqual(err,b'SYNTHETIC stderr')

    def test_stage_fixture_and_no_retry_on_failure(self):
        def synthetic_capture(argv,cwd,target,prompt=None,timeout=30):
            self.assertEqual(list(cwd.iterdir()),[])
            self.assertEqual(argv[-1],'-')
            self.assertNotIn(str(r.ROOT),argv)
            packet=r.strict_json(prompt.decode('utf-8'))
            self.assertEqual(packet['task_id'],'P01')
            target.mkdir()
            return dict(exit_code=1,timeout_or_interruption=False),b'',b'SYNTHETIC failed startup'
        with tempfile.TemporaryDirectory() as tmp:
            rows=[]
            with patch.object(r,'capture',side_effect=synthetic_capture) as c:
                with self.assertRaises(ValueError):
                    r.execute_stage('SYNTHETIC.exe',[],Path(tmp),rows,'P01','W','initial',['W-only','W-to-E'])
                self.assertEqual(c.call_count,1)
            self.assertEqual(len(rows),1)
            self.assertIsNone(rows[0]['telemetry']['usage']['input_tokens'])
            self.assertTrue((Path(tmp)/'ledger.jsonl').exists())

    def test_write_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json';r.write_json(p,{'synthetic':True})
            with self.assertRaises(FileExistsError):r.write_json(p,{})

    def test_frozen_tasks(self):
        self.assertEqual(r.sha((r.ROOT/'tasks.json').read_bytes()),r.TASK_SHA)


if __name__=='__main__':
    unittest.main(verbosity=2)

"""Targeted offline postmortem regressions; synthetic receipts, no processes."""
import argparse
from contextlib import contextmanager
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import cli_runner as r
import inspect_export as d
import test_cli_runner as fixtures

TIMEOUT = b'ERROR codex_models_manager::manager: failed to refresh available models: request timed out\n'
PRIVATE = b'C:\\Users\\SYNTHETIC_PRIVATE\\auth.json secret@example.invalid'


@contextmanager
def campaign(err=TIMEOUT, tail=b''):
    with fixtures.state() as (ledger, project):
        ledger.append('runtime',dict(version='0.159.2',executable_sha256=r.EXE_SHA))
        reservation = ledger.reserve('P01', 'W', r.sha(r.json_bytes(r.harness.packet('P01'))))
        target = ledger.directory / reservation['stage_id']; target.mkdir()
        out = fixtures.encode(fixtures.fixture('{"SYNTHETIC_wrong":true}')) + tail
        process = dict(exit_code=0, elapsed_seconds=0.25, timeout_or_interruption=False, launch_error=None)
        r.durable_bytes(target/'stdout.jsonl', out)
        r.durable_bytes(target/'stderr.log', err)
        ledger.append('completion', r.terminal_row(ledger.directory, reservation, process, out, err))
        r.safe_export(ledger, project, 'attempt_not_usable')
        (project/'.poc-state').mkdir()
        r.write_json(project/'.poc-state'/'owner.json', dict(schema_version=2, campaign='cap8-serial-public-toy-v2',
            data_directory_sha256=r.sha(os.path.normcase(str(ledger.directory.resolve())).encode('utf-8'))))
        yield ledger, project, target


class DiagnosticTests(unittest.TestCase):
    def test_catalog_timeout_keeps_cost_exit_and_all_private_sources_unchanged(self):
        with campaign(TIMEOUT + PRIVATE) as (ledger, project, target):
            paths = [ledger.path, target/'stdout.jsonl', target/'stderr.log', project/d.EXPORT/'latest.json']
            before = [p.read_bytes() for p in paths]
            result = d.inspect(project, ledger.directory)
            row = result['attempts'][0]
            self.assertEqual(result['budget']['consumed'], 3)
            self.assertEqual(result['budget']['remaining'], 5)
            self.assertEqual(row['stderr_codes'], ['model_catalog_refresh_request_timeout', 'unclassified_stderr'])
            self.assertEqual(row['exit_code'], 0)
            self.assertFalse(row['timeout_or_interruption'])
            self.assertEqual(row['stdout_errors'], [])
            self.assertEqual(row['error_event_counts'], {'error':0,'turn.failed':0,'item.error':0})
            self.assertEqual(row['incurred_usage']['input_tokens'], 100)
            self.assertFalse(row['usable']); self.assertFalse(row['visible_pass'])
            self.assertEqual(before, [p.read_bytes() for p in paths])
            pointer = r.strict_json((project/d.EXPORT/'diagnostic-latest.json').read_text(encoding='utf-8'))
            body = (project/d.EXPORT/pointer['path']).read_bytes()
            self.assertEqual(r.sha(body), pointer['sha256'])
            self.assertNotIn(PRIVATE, body)
            self.assertNotIn(b'SYNTHETIC_wrong', body)

    def test_receipt_tampering_cannot_replace_diagnostic(self):
        with campaign() as (ledger, project, target):
            d.inspect(project, ledger.directory)
            pointer = project/d.EXPORT/'diagnostic-latest.json'; before=pointer.read_bytes()
            (target/'stderr.log').write_bytes(b'SYNTHETIC altered')
            with self.assertRaisesRegex(r.Stop, 'diagnostic_receipt_integrity'):
                d.inspect(project, ledger.directory)
            self.assertEqual(pointer.read_bytes(), before)

    def test_pointer_rejects_traversal_and_snapshot_corruption(self):
        with campaign() as (ledger, project, target):
            pointer_path = project/d.EXPORT/'latest.json'
            pointer = r.strict_json(pointer_path.read_text(encoding='utf-8'))
            summary = project/d.EXPORT/pointer['files']['summary.json']['path']
            summary.write_bytes(b'{}')
            with self.assertRaisesRegex(r.Stop, 'diagnostic_snapshot_integrity'):
                d.snapshot(project)
            pointer['files']['summary.json']['path']='../private.json'
            pointer_path.write_bytes(r.json_bytes(pointer))
            with self.assertRaisesRegex(r.Stop, 'diagnostic_pointer_path'):
                d.snapshot(project)

    def test_data_directory_binding_and_ledger_chain_rejected(self):
        with campaign() as (ledger, project, target):
            owner=project/'.poc-state'/'owner.json'; original=owner.read_bytes()
            value=r.strict_json(original.decode()); value['data_directory_sha256']='0'*64
            owner.write_bytes(r.json_bytes(value))
            with self.assertRaisesRegex(r.Stop,'diagnostic_data_directory_binding'):
                d.inspect(project,ledger.directory)
            owner.write_bytes(original)
            value=r.strict_json(ledger.path.read_text(encoding='utf-8'))
            value['events'][-1]['payload']['process']['exit_code']=99
            ledger.path.write_bytes(r.json_bytes(value))
            with self.assertRaisesRegex(r.Stop,'ledger_integrity_failure'):
                d.inspect(project,ledger.directory)

    def test_malformed_tail_preserves_receipt_and_error_events(self):
        events=[dict(type='error',message='SYNTHETIC private'),dict(type='turn.failed',error={'message':'private'}),
                dict(type='item.completed',item=dict(type='error',message='SYNTHETIC private'))]
        with campaign(tail=fixtures.encode(events)+b'{broken\n') as (ledger, project, target):
            row=d.inspect(project,ledger.directory)['attempts'][0]
            self.assertEqual(row['error_event_counts'],{'error':1,'turn.failed':1,'item.error':1})
            self.assertIn('invalid_jsonl',row['stdout_errors'])
            self.assertEqual(row['incurred_usage']['input_tokens'],100)
            self.assertEqual(row['usage_status'],'partial')

    def test_process_metadata_cannot_export_private_strings(self):
        with campaign() as (ledger, project, target):
            row=ledger.rows()[-1]
            row['process']['elapsed_seconds']='SYNTHETIC private'
            with self.assertRaisesRegex(r.Stop,'diagnostic_process_schema'):
                d.attempt(row,(target/'stdout.jsonl').read_bytes(),(target/'stderr.log').read_bytes())

    def test_public_assessment_does_not_read_private_receipts_or_change_acceptance(self):
        with campaign() as (ledger, project, target):
            d.inspect(project,ledger.directory)
            # Saved safe sidecar is sufficient; private sources become unreadable JSON.
            ledger.path.write_bytes(b'SYNTHETIC invalid private ledger')
            (target/'stdout.jsonl').write_bytes(b'SYNTHETIC unavailable private receipt')
            with patch.object(d,'inspect',side_effect=AssertionError('Private reader forbidden')):
                result=d.assess_public(project)
            row=result['attempts'][0]
            self.assertEqual(row['semantic_runtime_status'],'completed_with_nonfatal_discovery_warning')
            self.assertEqual(row['assurance'],'reduced_catalog_freshness_unverified')
            self.assertFalse(row['recorded_usable']); self.assertFalse(row['visible_pass'])
            self.assertTrue(row['original_task_packet_hash_matches'])
            self.assertFalse(result['recorded_acceptance_changed'])
            self.assertEqual(result['budget']['remaining'],5)
            self.assertEqual(row['visible_failure_codes'],['unexpected_object_keys','intervals_not_list'])
            # Older sidecars lack checker codes: report the precise gap, never infer an answer.
            root=project/d.EXPORT; meta_path=root/'diagnostic-latest.json'
            meta=r.strict_json(meta_path.read_text(encoding='utf-8'))
            sidecar=r.strict_json((root/meta['path']).read_text(encoding='utf-8'))
            del sidecar['attempts'][0]['visible_failure_codes']
            body=r.json_bytes(sidecar); digest=r.sha(body)
            r.durable_bytes(root/'diagnostics'/(digest+'.json'),body)
            meta.update(path='diagnostics/'+digest+'.json',sha256=digest)
            meta_path.write_bytes(r.json_bytes(meta))
            gap=d.assess_public(project)['attempts'][0]
            self.assertEqual(gap['exact_visible_failure'],'unavailable_in_safe_export')
            self.assertIsNone(gap['visible_failure_codes'])

    def test_public_assessment_unknown_stderr_and_runtime_errors_remain_blocking(self):
        error=fixtures.encode([dict(type='error',message='SYNTHETIC private error')])
        for err,tail in ((TIMEOUT+PRIVATE,b''),(TIMEOUT,error),(b'Code Mode is unavailable',b'')):
            with self.subTest(err=err[:20]),campaign(err,tail) as (ledger,project,target):
                d.inspect(project,ledger.directory)
                row=d.assess_public(project)['attempts'][0]
                self.assertEqual(row['semantic_runtime_status'],'blocking_or_unclassified')

    def test_public_assessment_rejects_stale_sidecar_binding(self):
        with campaign() as (ledger,project,target):
            d.inspect(project,ledger.directory)
            path=project/d.EXPORT/'diagnostic-latest.json'
            value=r.strict_json(path.read_text(encoding='utf-8')); value['summary_sha256']='0'*64
            path.write_bytes(r.json_bytes(value))
            with self.assertRaisesRegex(r.Stop,'diagnostic_sidecar_binding'):
                d.assess_public(project)

    def test_p01_public_contract_touching_overlap_empty_and_json_are_distinct(self):
        self.assertTrue(r.harness.visible('P01',{'intervals':[[0,4],[4,5],[8,12]]})['pass'])
        self.assertEqual(d.p01_visible_codes({'intervals':[[0,4],[4,5],[8,12]]}),[])
        # Visible structure deliberately does not certify original coverage/correctness.
        self.assertTrue(r.harness.visible('P01',{'intervals':[]})['pass'])
        self.assertFalse(r.harness.grade('P01',{'intervals':[]}))
        for candidate in ({'wrong_key':[]},{'intervals':[[7,7]]},{'intervals':[[8,12],[0,4]]},
                          {'intervals':[[0,4],[3,6]]},{'intervals':[[False,4]]}):
            with self.subTest(candidate=candidate):
                self.assertFalse(r.harness.visible('P01',candidate)['pass'])
                self.assertTrue(d.p01_visible_codes(candidate))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(DiagnosticTests)
    stream=io.StringIO()
    with patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess permitted')):
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    evidence=dict(kind='OFFLINE_DIAGNOSTIC_REGRESSION_ONLY',status='passed' if result.wasSuccessful() else 'failed',
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        failed_tests=[test.id() for test,_ in result.failures+result.errors],optimization=sys.flags.optimize,
        new_inference_launches=0,source_hashes={name:r.sha((r.ROOT/name).read_bytes())
            for name in ('inspect_export.py','test_inspect_export.py')})
    r.durable_bytes(args.out,r.json_bytes(evidence),replace=True)
    print(stream.getvalue()); print(r.json_bytes(evidence).decode())
    raise SystemExit(0 if result.wasSuccessful() else 1)

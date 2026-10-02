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
        reservation = ledger.reserve('P01', 'W', r.sha(b'SYNTHETIC prompt'))
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

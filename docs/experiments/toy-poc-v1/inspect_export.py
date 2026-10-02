"""Read-only receipt diagnosis; publish allowlisted codes, never raw logs."""
import argparse
import math
import os
from pathlib import Path
import re

import cli_runner as r

EXPORT = 'poc-exports/cap8-serial-public-toy-v2'


def snapshot(project):
    root = r.no_links(Path(project) / EXPORT)
    pointer_bytes = (root / 'latest.json').read_bytes()
    pointer = r.strict_json(pointer_bytes.decode('utf-8'))
    if (set(pointer) != {'schema_version', 'files'} or pointer['schema_version'] != 2
        or set(pointer['files']) != {'summary.json', 'report-en.md', 'report-ru.md'}):
        raise r.Stop('diagnostic_pointer_schema')
    summary = None
    for name, entry in pointer['files'].items():
        if (set(entry) != {'path', 'sha256'} or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256'])
            or not re.fullmatch(r'snapshots/[0-9a-f]{64}/' + re.escape(name), entry['path'])):
            raise r.Stop('diagnostic_pointer_path')
        body = r.no_links(root / entry['path']).read_bytes()
        if r.sha(body) != entry['sha256']:
            raise r.Stop('diagnostic_snapshot_integrity')
        if name == 'summary.json':
            summary = r.strict_json(body.decode('utf-8'))
    r.validate_export(summary)
    return root, pointer_bytes, pointer['files']['summary.json']['sha256'], summary


def stderr_codes(data):
    text = data.decode('utf-8', errors='replace')
    codes = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        if (re.search(r'\bcodex_models_manager::manager:', line)
            and line.lower().rstrip().endswith('failed to refresh available models: request timed out')):
            codes.add('model_catalog_refresh_request_timeout')
        elif 'model rerouted:' in line.lower():
            codes.add('model_rerouted')
        elif 'Code Mode is unavailable' in line:
            codes.add('code_mode_unavailable')
        else:
            codes.add('unclassified_stderr')
    return sorted(codes)


def attempt(row, out, err):
    if r.sha(out) != row['stdout_sha256'] or r.sha(err) != row['stderr_sha256']:
        raise r.Stop('diagnostic_receipt_integrity')
    process = row['process']
    if (process.get('exit_code') is not None and type(process['exit_code']) is not int
        or type(process.get('elapsed_seconds')) not in (int, float)
        or not math.isfinite(process['elapsed_seconds']) or process['elapsed_seconds'] < 0
        or type(process.get('timeout_or_interruption', False)) is not bool
        or type(row['telemetry']['valid']) is not bool):
        raise r.Stop('diagnostic_process_schema')
    parsed = r.parse_events(out, process.get('exit_code'), process.get('timeout_or_interruption', False))
    counts = {'error': 0, 'turn.failed': 0, 'item.error': 0}
    for line in out.splitlines():
        try:
            event = r.strict_json(line.decode('utf-8-sig'))
        except (ValueError, UnicodeError):
            continue
        if type(event) is not dict:
            continue
        if event.get('type') in ('error', 'turn.failed'):
            counts[event['type']] += 1
        if str(event.get('type')).startswith('item.') and type(event.get('item')) is dict:
            counts['item.error'] += int(event['item'].get('type') == 'error')
    candidate = None
    json_status = 'no_agent_message'
    if parsed['answer'] is not None:
        try:
            candidate = r.strict_json(parsed['answer'])
            json_status = 'object' if type(candidate) is dict else 'other_json'
        except ValueError:
            json_status = 'invalid_json'
    visible = r.harness.visible(row['task_id'], candidate)['pass']
    return dict(attempt_id=row['stage_id'], exit_code=process.get('exit_code'),
        elapsed_seconds=process.get('elapsed_seconds'),
        timeout_or_interruption=process.get('timeout_or_interruption', False),
        launch_error_present=process.get('launch_error') is not None,
        stdout_runtime_status=parsed['runtime_status'], stdout_errors=parsed['errors'],
        error_event_counts=counts, stderr_codes=stderr_codes(err), stderr_bytes=len(err),
        stderr_sha256=r.sha(err), stdout_sha256=r.sha(out),
        usage_status=parsed['usage_status'], incurred_usage=parsed['usage'],
        candidate_json_status=json_status, visible_pass=visible,
        usable=row['telemetry']['valid'], acceptance_runtime_status=row['telemetry']['runtime_status'])


def inspect(project, directory):
    project, directory = r.no_links(project), r.no_links(directory)
    root, pointer_bytes, summary_sha, summary = snapshot(project)
    identity = dict(schema_version=2, campaign='cap8-serial-public-toy-v2',
        data_directory_sha256=r.sha(os.path.normcase(str(directory.resolve())).encode('utf-8')))
    if r.strict_json((project / '.poc-state' / 'owner.json').read_text(encoding='utf-8')) != identity:
        raise r.Stop('diagnostic_data_directory_binding')
    path = r.no_links(directory / 'ledger.json')
    ledger_bytes = path.read_bytes()
    data = r.strict_json(ledger_bytes.decode('utf-8'))
    previous = None
    for n, event in enumerate(data['events']):
        payload = {k: v for k, v in event.items() if k != 'sha256'}
        if event['seq'] != n or event['previous'] != previous or event['sha256'] != r.sha(r.json_bytes(payload)):
            raise r.Stop('ledger_integrity_failure')
        previous = event['sha256']
    # Reuse row validation without calling the constructor that can initialize a ledger.
    ledger = object.__new__(r.Ledger)
    ledger.data = data
    rows = ledger.rows()
    if len(rows) != summary['budget']['consumed'] or data['manifest']['source_hashes'] != summary['source_hashes']:
        raise r.Stop('diagnostic_summary_ledger_mismatch')
    exported = {a['attempt_id']: a for a in summary['attempts']}
    results = []
    for row in rows:
        if row.get('imported_prior_failure'):
            continue
        if not re.fullmatch(r'P0[123]-[WE]-a0[12]', row['stage_id']) or row['state'] != 'recorded':
            raise r.Stop('diagnostic_partial_attempt')
        public = exported[row['stage_id']]
        for key in ('stdout_sha256', 'stderr_sha256'):
            if public[key] != row[key]:
                raise r.Stop('diagnostic_summary_ledger_mismatch')
        if public['runtime_status'] != row['telemetry']['runtime_status'] or public['usable'] != row['telemetry']['valid']:
            raise r.Stop('diagnostic_summary_ledger_mismatch')
        target = r.no_links(directory / row['stage_id'])
        results.append(attempt(row, r.no_links(target / 'stdout.jsonl').read_bytes(),
                               r.no_links(target / 'stderr.log').read_bytes()))
    if path.read_bytes() != ledger_bytes or (root / 'latest.json').read_bytes() != pointer_bytes:
        raise r.Stop('diagnostic_source_changed')
    result = dict(schema_version=1, evidence_kind='OBSERVED_SAVED_RECEIPTS_NO_INFERENCE',
        summary_sha256=summary_sha, ledger_sha256=r.sha(ledger_bytes), budget=summary['budget'],
        attempts=results, new_inference_launches=0, raw_private_content_exported=False)
    body = r.json_bytes(result)
    dest = r.no_links(root / 'diagnostics' / (r.sha(body) + '.json'))
    dest.parent.mkdir(exist_ok=True)
    if dest.exists():
        if dest.read_bytes() != body:
            raise r.Stop('diagnostic_export_integrity')
    else:
        r.durable_bytes(dest, body)
    r.durable_bytes(root / 'diagnostic-latest.json', r.json_bytes(dict(schema_version=1,
        path='diagnostics/' + dest.name, sha256=r.sha(body), summary_sha256=summary_sha)), replace=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(r.json_bytes(inspect(r.PROJECT, args.data_dir)).decode('utf-8'))
    except (r.Stop, OSError, ValueError, KeyError):
        print('STOP: diagnostic_integrity_or_schema_failure')
        raise SystemExit(2)

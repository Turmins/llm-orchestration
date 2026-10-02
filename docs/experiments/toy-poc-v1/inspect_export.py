"""Read-only receipt diagnosis; publish allowlisted codes, never raw logs."""
import argparse
import math
import os
from pathlib import Path
import re

import cli_runner as r

EXPORT = 'poc-exports/cap8-serial-public-toy-v2'
VISIBLE_CODES = {'candidate_not_object', 'unexpected_object_keys', 'intervals_not_list',
    'invalid_interval_pair', 'nonpositive_interval', 'intervals_not_sorted',
    'adjacent_intervals_overlap', 'visible_contract_failed'}


def p01_visible_codes(candidate):
    """Only public structural rules; no original coverage or hidden reference."""
    if type(candidate) is not dict:
        return ['candidate_not_object']
    codes = [] if set(candidate) == {'intervals'} else ['unexpected_object_keys']
    xs = candidate.get('intervals')
    if type(xs) is not list:
        return codes + ['intervals_not_list']
    if not all(type(x) is list and len(x) == 2 and all(type(v) is int for v in x) for x in xs):
        return codes + ['invalid_interval_pair']
    if not all(a < b for a, b in xs):
        codes.append('nonpositive_interval')
    if xs != sorted(xs):
        codes.append('intervals_not_sorted')
    elif any(a[1] > b[0] for a, b in zip(xs, xs[1:])):
        codes.append('adjacent_intervals_overlap')
    return codes


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
        visible_failure_codes=p01_visible_codes(candidate) if row['task_id'] == 'P01'
                              else [] if visible else ['visible_contract_failed'],
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


def assess_public(project):
    """Source-backed semantics from safe exports only; never reopen private receipts."""
    root, unused_pointer, summary_sha, summary = snapshot(project)
    meta = r.strict_json((root / 'diagnostic-latest.json').read_text(encoding='utf-8'))
    if (set(meta) != {'schema_version', 'path', 'sha256', 'summary_sha256'}
        or meta['schema_version'] != 1 or meta['summary_sha256'] != summary_sha
        or not re.fullmatch(r'diagnostics/[0-9a-f]{64}\.json', meta['path'])):
        raise r.Stop('diagnostic_sidecar_binding')
    body = r.no_links(root / meta['path']).read_bytes()
    if r.sha(body) != meta['sha256']:
        raise r.Stop('diagnostic_sidecar_integrity')
    diagnostic = r.strict_json(body.decode('utf-8'))
    if diagnostic['summary_sha256'] != summary_sha or diagnostic['budget'] != summary['budget']:
        raise r.Stop('diagnostic_sidecar_binding')
    details = {a['attempt_id']: a for a in diagnostic['attempts']}
    attempts = []
    for attempt in summary['attempts']:
        if attempt['stage'] == 'historical':
            continue
        detail = details[attempt['attempt_id']]
        if any(detail[key] != attempt[key] for key in ('stdout_sha256', 'stderr_sha256', 'exit_code')):
            raise r.Stop('diagnostic_sidecar_binding')
        if detail['visible_pass'] != attempt['visible_pass'] or detail['incurred_usage'] != attempt['usage']:
            raise r.Stop('diagnostic_sidecar_binding')
        known = (summary['settings']['cli_version'] == '0.159.2'
            and summary['settings']['cli_sha256'] == r.EXE_SHA
            and detail['stderr_codes'] == ['model_catalog_refresh_request_timeout']
            and detail['stdout_runtime_status'] == 'completed' and detail['stdout_errors'] == []
            and detail['error_event_counts'] == {'error': 0, 'turn.failed': 0, 'item.error': 0}
            and all(type(x) is int for x in detail['error_event_counts'].values())
            and type(detail['exit_code']) is int and detail['exit_code'] == 0
            and detail['timeout_or_interruption'] is False and detail['launch_error_present'] is False
            and detail['usage_status'] == 'reported_complete_stage'
            and attempt['safety_status'] != 'tool_violation')
        expected_prompt_sha = r.sha(r.json_bytes(r.harness.packet(attempt['task_id'])))
        visible_codes = detail.get('visible_failure_codes')
        if visible_codes is not None and (type(visible_codes) is not list
            or any(type(code) is not str or code not in VISIBLE_CODES for code in visible_codes)
            or bool(visible_codes) == (attempt['visible_pass'] is True)):
            raise r.Stop('diagnostic_visible_code_schema')
        attempts.append(dict(attempt_id=attempt['attempt_id'],
            semantic_runtime_status='completed_with_nonfatal_discovery_warning' if known else 'blocking_or_unclassified',
            assurance='reduced_catalog_freshness_unverified' if known else 'not_reassessed',
            recorded_runtime_status=attempt['runtime_status'], recorded_usable=attempt['usable'],
            visible_pass=attempt['visible_pass'],
            original_task_packet_hash_matches=attempt['stage'] == 'initial' and expected_prompt_sha == attempt['prompt_sha256'],
            exact_visible_failure='checker_reason_codes_available' if visible_codes is not None
                                  else 'unavailable_in_safe_export' if attempt['visible_pass'] is False else None,
            visible_failure_codes=visible_codes,
            missing_visible_evidence=['per_check_failure_codes_or_hash_bound_candidate']
                                     if attempt['visible_pass'] is False and visible_codes is None else [],
            actual_model_verified=False, effective_tool_mode_verified=False))
    result = dict(schema_version=1, evidence_kind='SAFE_EXPORT_SOURCE_BACKED_ASSESSMENT',
        summary_sha256=summary_sha, diagnostic_sha256=meta['sha256'], budget=summary['budget'],
        attempts=attempts, new_inference_launches=0, recorded_acceptance_changed=False)
    r.durable_bytes(root / 'assessment-latest.json', r.json_bytes(result), replace=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--public-only', action='store_true', help='Assess existing safe exports; no private receipt access')
    args = parser.parse_args()
    if not args.public_only and args.data_dir is None:
        parser.error('--data-dir is required unless --public-only is selected')
    if args.public_only and args.data_dir is not None:
        parser.error('--public-only must not receive a private data directory')
    try:
        result = assess_public(r.PROJECT) if args.public_only else inspect(r.PROJECT, args.data_dir)
        print(r.json_bytes(result).decode('utf-8'))
    except (r.Stop, OSError, ValueError, KeyError):
        print('STOP: diagnostic_integrity_or_schema_failure')
        raise SystemExit(2)

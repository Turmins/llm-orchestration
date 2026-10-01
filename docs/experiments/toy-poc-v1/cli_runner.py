"""Minimal serial subscription CLI controller; stdlib, Python >=3.9.
Default mode never runs inference. One explicit persistent data directory owns
the cap8 budget across restarts. Raw bytes stay private; exports are allowlisted.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

import harness

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
TASK_SHA = '9139a16cfc067e875d55f0af3bc6720d125615e9c12aa4d573c577b2de5875b4'
MODELS = {'W': 'gpt-6-luna', 'E': 'gpt-6.1-sol'}
EXE_SHA = '34549ded6e2aee87c911c62d025e52e26c488683d0f489cd68f756baef1a6df6'
FIELDS = ('input_tokens', 'output_tokens', 'cached_input_tokens',
          'cache_write_input_tokens', 'reasoning_output_tokens')
LIMITS = dict(stages=8, seconds_per_stage=180, input_per_stage=32000,
              output_per_stage=4000, input_overall=384000, output_overall=48000,
              prompt_utf8_bytes=16000, controller_retries=0)
# Preserve capability restrictions; no tool-mode selector or host override.
DISABLE = ('shell_tool', 'unified_exec', 'apps', 'plugins', 'multi_agent',
           'multi_agent_v2', 'browser_use', 'browser_use_external',
           'browser_use_full_cdp_access', 'computer_use', 'view_image', 'memories',
           'hooks', 'skill_mcp_dependency_install', 'skill_search', 'tool_suggest',
           'unbounded_connection_retries')
CONTRACT = 'https://github.com/openai/codex/blob/rust-v0.159.2/codex-rs/exec/src/exec_events.rs'


class Stop(ValueError):
    """Stable safe reason code. Raw diagnostic messages never enter exports."""


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True,
                       indent=2, allow_nan=False) + '\n').encode('utf-8')


def strict_json(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate JSON key')
            result[k] = v
        return result
    def bad(value):
        raise ValueError('nonfinite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad)


def no_links(path):
    """Reject symlinks and Windows junctions, including existing ancestors."""
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            st = part.lstat()
            if part.is_symlink() or getattr(st, 'st_file_attributes', 0) & 0x400:
                raise Stop('linked_path_rejected')
    return path


def durable_bytes(path, data, replace=False):
    path = no_links(path)
    if not replace:
        with path.open('xb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        return
    fd, name = tempfile.mkstemp(prefix='.atomic-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
        if os.name != 'nt':
            directory = os.open(str(path.parent), os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)  # Only this function's newly generated temp file.


def write_json(path, data):
    durable_bytes(path, json_bytes(data))


@contextmanager
def exclusive_lock(directory):
    directory = no_links(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with no_links(directory / 'controller.lock').open('a+b') as f:
        if f.tell() == 0:
            f.write(b'0'); f.flush(); os.fsync(f.fileno())
        f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            raise Stop('controller_already_locked') from e
        try:
            yield
        finally:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def parse_events(data, exit_code, timed_out=False):
    """Incremental observations: malformed tails/errors cannot erase usage."""
    errors, events, observations = [], [], []
    offset = 0
    for number, line in enumerate(data.splitlines(keepends=True), 1):
        try:
            text = line.decode('utf-8-sig' if number == 1 else 'utf-8')
            if text.strip():
                event = strict_json(text)
                if type(event) is not dict:
                    raise ValueError('non-object event')
                events.append(event)
                if type(event.get('usage')) is dict:
                    raw = event['usage']
                    counters = {}
                    for k in FIELDS:
                        v = raw.get(k)
                        counters[k] = v if type(v) is int and v >= 0 else None
                        if v is not None and counters[k] is None:
                            errors.append('invalid_counter')
                    observations.append(dict(line=number, byte_offset=offset,
                        line_sha256=sha(line), source_sha256=sha(data),
                        event_type=str(event.get('type')), usage=counters,
                        raw_usage=raw, receipt_sha256=sha(json_bytes(raw))))
        except (ValueError, UnicodeError):
            errors.append('invalid_jsonl')
        offset += len(line)
    receipts = {o['receipt_sha256']: o for o in observations}
    # Quarantine conflicts; retain all observations. The minimum is a lower
    # bound, never a complete total. Receipt replays are never summed.
    usage = {k: min((o['usage'][k] for o in receipts.values()
                    if o['usage'][k] is not None), default=None) for k in FIELDS}
    completed = [e for e in events if e.get('type') == 'turn.completed']
    threads = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
    starts = [e for e in events if e.get('type') == 'turn.started']
    if (len({sha(json_bytes(e)) for e in completed}) != 1 or len(starts) != 1
        or len(threads) != 1 or not threads[0]):
        errors.append('fresh_turn_incomplete')
    if events and (events[0].get('type') != 'thread.started' or events[-1].get('type') != 'turn.completed'):
        errors.append('event_boundaries')
    if len(receipts) > 1:
        errors.append('conflicting_usage')
    if any(usage[k] is None for k in ('input_tokens', 'output_tokens')):
        errors.append('required_usage_missing')
    if usage['input_tokens'] == 0:
        errors.append('zero_input_unmeasured')
    for component, total in [('cached_input_tokens', 'input_tokens'),
                             ('cache_write_input_tokens', 'input_tokens'),
                             ('reasoning_output_tokens', 'output_tokens')]:
        if any(o['usage'][component] is not None and o['usage'][total] is not None
               and o['usage'][component] > o['usage'][total] for o in observations):
            errors.append('component_exceeds_total')
    accounting_errors = set(errors)
    answers, diagnostics, safety = [], [], 'unverified_boundary'
    allowed_events = {'thread.started', 'turn.started', 'turn.completed',
                      'item.started', 'item.updated', 'item.completed'}
    for event in events:
        kind = event.get('type')
        if kind not in allowed_events:
            diagnostics.append('runtime_error' if kind in ('error', 'turn.failed') else 'unknown_event')
        if str(kind).startswith('item.'):
            item = event.get('item')
            if type(item) is not dict:
                diagnostics.append('invalid_item'); continue
            if item.get('type') == 'error':
                message = str(item.get('message', ''))
                diagnostics.append('capability_unavailable' if 'Code Mode is unavailable' in message
                                   else 'rerouted' if 'model rerouted:' in message.lower()
                                   else 'unknown_diagnostic')
            elif item.get('type') not in ('agent_message', 'reasoning'):
                safety = 'tool_violation'
            elif kind == 'item.completed' and item.get('type') == 'agent_message':
                answers.append(item.get('text'))
    answer = answers[-1] if answers and isinstance(answers[-1], str) else None
    if exit_code != 0 or timed_out:
        runtime = 'interrupted' if timed_out else 'exit_unknown' if exit_code is None else 'process_failed'
    elif diagnostics:
        runtime = diagnostics[0]
    elif not completed or answer is None:
        runtime = 'incomplete'
    else:
        runtime = 'completed'
    coverage = ('conflicting' if len(receipts) > 1 else 'missing' if not receipts else
                'partial' if accounting_errors or exit_code != 0 or timed_out else 'reported_complete_stage')
    valid = runtime == 'completed' and coverage == 'reported_complete_stage' and safety != 'tool_violation'
    return dict(valid=valid, runtime_status=runtime, safety_status=safety, usage_status=coverage,
        errors=sorted(set(errors + diagnostics)), usage=usage,
        raw_usage=next(iter(receipts.values()))['raw_usage'] if len(receipts) == 1 else None,
        usage_observations=observations, thread_id=threads[0] if len(threads) == 1 else None,
        answer=answer, actual_model=None, model_attribution='UNVERIFIED',
        scope='fresh_thread_single_turn_stage', network_request_count=None,
        source='documented_cli_runtime_event', source_contract_ref=CONTRACT)


def totals(rows):
    unique = {}
    for row in rows:
        key = row['stage_id']
        if key in unique and unique[key] != row:
            raise Stop('conflicting_attempt_replay')
        unique[key] = row
    rows = list(unique.values())
    complete = all(r['telemetry']['usage_status'] == 'reported_complete_stage' for r in rows)
    result = dict(stages=len(rows), complete=complete,
                  unresolved_attempts=sum(r['telemetry']['usage_status'] != 'reported_complete_stage' for r in rows))
    for k in FIELDS:
        xs = [r['telemetry']['usage'][k] for r in rows]
        result[k] = sum(xs) if complete and all(x is not None for x in xs) else None
        result[k + '_known_subtotal'] = sum(x for x in xs if x is not None)
    result['input_plus_output'] = (result['input_tokens'] + result['output_tokens']
        if result['input_tokens'] is not None and result['output_tokens'] is not None else None)
    result.update(actual_model_verified=False, subscription_allowance=None, api_charge=None)
    return result


def source_manifest():
    if sha((ROOT / 'tasks.json').read_bytes()) != TASK_SHA:
        raise Stop('frozen_task_bytes_changed')
    plan = strict_json((ROOT / 'small-test-plan.json').read_text(encoding='utf-8'))
    if (plan['task_order'] != ['P01', 'P02', 'P03'] or plan['budget_cap'] != 8
        or plan['max_new_launches'] != 6 or plan['models'] != MODELS):
        raise Stop('unsupported_plan')
    hashes = {}
    for name in ('cli_runner.py', 'harness.py', 'run-poc.ps1', 'tasks.json', 'small-test-plan.json'):
        raw = (ROOT / name).read_bytes()
        hashes[name] = dict(working_tree_sha256=sha(raw), lf_sha256=sha(raw.replace(b'\r\n', b'\n')))
    return dict(schema_version=2, plan=plan, source_hashes=hashes, limits=LIMITS,
                evidence_kind='subscription_cli_and_user_report', source_contract=CONTRACT)


def legacy_rows(path):
    raw_file = Path(path).read_bytes()
    evidence = strict_json(raw_file.decode('utf-8-sig'))
    stages = evidence['failed_stages']
    expected = {'budget_cap': 8, 'reported_consumed_cli_launches': 2,
                'max_remaining_new_cli_launches': 6}
    if any(type(evidence[k]) is not int or evidence[k] != v for k, v in expected.items()) or len(stages) != 2:
        raise Stop('legacy_budget_inconsistent')
    rows = []
    for item in stages:
        role = item['role']
        if (item['task_id'] != 'P01' or role not in MODELS
            or type(item['cli_launches']) is not int or item['cli_launches'] != 1
            or item['source'] != 'user-supplied evidence'):
            raise Stop('legacy_provenance_invalid')
        usage = {k: item['usage'].get(k) for k in FIELDS}
        if any(v is not None and (type(v) is not int or v < 0) for v in usage.values()):
            raise Stop('legacy_counter_invalid')
        body = json_bytes(item['candidate'])
        rows.append(dict(stage_id='legacy-P01-' + role, task_id='P01', role=role,
            stage='historical', attempt=1, state='recorded', imported_prior_failure=True,
            requested_model=MODELS[role], actual_model=None,
            candidate=item['candidate'], candidate_sha256=sha(body), candidate_artifact=None,
            candidate_representation='reconstructed_user_report_utf8_json',
            prompt_sha256=None, stdout_sha256=None, stderr_sha256=None,
            process=dict(exit_code=item.get('cli_exit_code'),
                         elapsed_seconds=item.get('process', {}).get('elapsed_seconds')),
            telemetry=dict(valid=False, runtime_status='capability_unavailable',
                safety_status='unverified_boundary', usage_status='user_reported_partial',
                usage=usage, usage_observations=[], actual_model=None,
                source='user-supplied evidence', source_sha256=sha(raw_file)),
            provenance=dict(source='user-supplied evidence', source_sha256=sha(raw_file),
                            original_raw_artifacts_available=False)))
    if {r['role'] for r in rows} != {'W', 'E'}:
        raise Stop('duplicate_legacy_attempt')
    return rows


class Ledger:
    """Hold exclusive_lock for the entire controller lifetime, including export.
    Atomic JSON snapshot of an append-only hash chain avoids partial JSONL tails.
    Corruption fails closed; never replace a damaged ledger with a new budget.
    """
    def __init__(self, directory, manifest, prior_path=ROOT / 'failed-launches-user-ledger.json'):
        self.directory = no_links(directory)
        self.path = no_links(self.directory / 'ledger.json')
        if self.path.exists():
            self.data = strict_json(self.path.read_text(encoding='utf-8'))
            if self.data['manifest'] != manifest:
                raise Stop('resume_manifest_changed')
            previous = None
            for n, event in enumerate(self.data['events']):
                payload = {k: v for k, v in event.items() if k != 'sha256'}
                if event['seq'] != n or event['previous'] != previous or event['sha256'] != sha(json_bytes(payload)):
                    raise Stop('ledger_integrity_failure')
                previous = event['sha256']
            self.rows()
        else:
            self.data = dict(manifest=manifest, events=[])
            for row in legacy_rows(prior_path):
                self._event('legacy', row)
            self.save()

    def _event(self, kind, payload):
        events = self.data['events']
        event = dict(seq=len(events), previous=events[-1]['sha256'] if events else None,
                     type=kind, payload=payload)
        event['sha256'] = sha(json_bytes(event))
        events.append(event)

    def save(self):
        durable_bytes(self.path, json_bytes(self.data), replace=True)

    def append(self, kind, payload):
        self._event(kind, payload)
        try:
            self.save()
        except BaseException:
            self.data['events'].pop()
            raise

    def rows(self):
        rows = {}
        legacy = set()
        for event in self.data['events']:
            kind, payload = event['type'], event['payload']
            if kind in ('legacy', 'reservation'):
                key = payload['stage_id']
                if key in rows:
                    raise Stop('duplicate_ledger_reservation')
                rows[key] = payload
                if kind == 'legacy':
                    legacy.add(key)
            elif kind in ('completion', 'recovery'):
                key = payload['stage_id']
                if key not in rows or rows[key].get('imported_prior_failure'):
                    raise Stop('completion_without_reservation')
                if rows[key]['state'] == 'recorded':
                    raise Stop('duplicate_terminal_record')
                rows[key] = payload
            elif kind not in ('runtime', 'process_started'):
                raise Stop('unknown_ledger_event')
        if legacy != {'legacy-P01-W', 'legacy-P01-E'} or len(rows) > 8:
            raise Stop('ledger_integrity_failure')
        return list(rows.values())

    def reserve(self, task, role, prompt_sha, parent=None):
        if task not in self.data['manifest']['plan']['task_order'] or role not in MODELS:
            raise Stop('attempt_outside_plan')
        ident = task + '-' + role + ('-a02' if role == 'E' else '-a01')
        rows = self.rows()
        if any(r['stage_id'] == ident for r in rows):
            raise Stop('duplicate_invocation')
        if len(rows) >= LIMITS['stages']:
            raise Stop('budget_exhausted')
        if any(not r.get('imported_prior_failure') and not r['telemetry']['valid'] for r in rows):
            raise Stop('unusable_prior_attempt')
        if any(r['telemetry']['usage'][k] is None for r in rows for k in ('input_tokens', 'output_tokens')):
            raise Stop('prior_usage_unknown')
        total = totals(rows)
        if (total['input_tokens_known_subtotal'] >= LIMITS['input_overall']
            or total['output_tokens_known_subtotal'] >= LIMITS['output_overall']):
            raise Stop('overall_token_threshold')
        if role == 'E':
            parents = [r for r in rows if r['stage_id'] == parent]
            if (len(parents) != 1 or parents[0]['task_id'] != task or parents[0]['role'] != 'W'
                or harness.visible(task, parents[0]['candidate'])['pass']):
                raise Stop('invalid_takeover_parent')
        elif parent is not None:
            raise Stop('invalid_initial_parent')
        row = dict(stage_id=ident, task_id=task, role=role, attempt=2 if role == 'E' else 1,
            stage='takeover' if role == 'E' else 'initial', parent_stage_id=parent,
            state='reserved', requested_model=MODELS[role], actual_model=None,
            prompt_sha256=prompt_sha, candidate=None, candidate_sha256=None,
            candidate_artifact=None, stdout_sha256=None, stderr_sha256=None,
            process=dict(exit_code=None, elapsed_seconds=None),
            telemetry=dict(valid=False, runtime_status='not_observed', safety_status='unverified_boundary',
                usage_status='missing', usage={k: None for k in FIELDS}, usage_observations=[],
                source='launch_reservation'))
        self.append('reservation', row)  # Durable BEFORE Popen.
        return row


def base_args(exe, disabled):
    args = [exe, '--ask-for-approval', 'never', 'exec', '--json', '--ephemeral',
            '--ignore-user-config', '--skip-git-repo-check', '--sandbox', 'read-only']
    # Retain isolation from arbitrary user MCP/hooks/instructions. Auth is CLI-owned.
    # A host depending on excluded user config remains a runtime prerequisite.
    for setting in ('forced_login_method="chatgpt"', 'model_provider="openai"',
                    'model_reasoning_effort="medium"', 'service_tier="default"',
                    'web_search="disabled"', 'project_doc_max_bytes=0', 'agents.enabled=false'):
        args += ['-c', setting]
    for feature in disabled:
        args += ['--disable', feature]
    return args


def capture(argv, cwd, target, prompt=None, timeout=30, on_started=None):
    target.mkdir(exist_ok=True)
    start, stamp = time.monotonic(), now()
    code, interrupted, launch_error = None, False, None
    with (target / 'stdout.jsonl').open('xb') as out, (target / 'stderr.log').open('xb') as err:
        proc = None
        try:
            proc = subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.PIPE,
                                    stdout=out, stderr=err, shell=False)
            if on_started:
                on_started()
            try:
                proc.communicate(input=prompt, timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                interrupted = True
                proc.kill(); proc.wait()  # Only this call's own child.
            code = proc.returncode
        except OSError as e:
            launch_error = type(e).__name__
        except BaseException:
            if proc is not None and proc.poll() is None:
                proc.kill(); proc.wait()
            raise
        finally:
            out.flush(); os.fsync(out.fileno()); err.flush(); os.fsync(err.fileno())
    result = dict(started_at=stamp, ended_at=now(), elapsed_seconds=time.monotonic()-start,
                  exit_code=code, timeout_or_interruption=interrupted, launch_error=launch_error)
    write_json(target / 'process.json', result)
    return result, (target / 'stdout.jsonl').read_bytes(), (target / 'stderr.log').read_bytes()


def preflight(exe, directory):
    if sys.version_info < (3, 9):
        raise Stop('python_3_9_required')
    if any(os.environ.get(k) for k in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL')):
        raise Stop('api_environment_override')
    found = shutil.which(exe)
    if not found or Path(found).suffix.lower() != '.exe':
        raise Stop('native_codex_exe_required')
    if sha(Path(found).read_bytes()) != EXE_SHA:
        raise Stop('cli_executable_mismatch')
    texts = {}
    check = Path(tempfile.mkdtemp(prefix='preflight-', dir=str(directory)))
    for name, tail in [('version', ['--version']), ('help', ['--help']),
                       ('exec-help', ['exec', '--help']), ('login', ['login', 'status']),
                       ('features', ['features', 'list'])]:
        process, out, err = capture([found] + tail, check, check / name)
        if process['exit_code'] != 0:
            raise Stop('preflight_failed')
        texts[name] = (out + err).decode('utf-8', errors='replace')
    if not re.search(r'codex-cli\s+0\.159\.2(?:\s|$)', texts['version']):
        raise Stop('cli_version_mismatch')
    if 'Logged in using ChatGPT' not in texts['login']:
        raise Stop('ordinary_user_chatgpt_auth_required')
    for flag in ('--json', '--model', '--ephemeral', '--ignore-user-config', '--skip-git-repo-check', '--sandbox'):
        if flag not in texts['exec-help']:
            raise Stop('required_exec_flag_missing')
    if any(flag not in texts['help'] for flag in ('--ask-for-approval', '--disable')):
        raise Stop('required_global_flag_missing')
    features = {line.split()[0] for line in texts['features'].splitlines() if line.strip()}
    if not {'shell_tool', 'unified_exec', 'apps', 'plugins', 'multi_agent'} <= features:
        raise Stop('required_tool_restriction_missing')
    disabled = [x for x in DISABLE if x in features]
    return found, disabled, dict(version='0.159.2', executable_sha256=sha(Path(found).read_bytes()),
        disabled_features=disabled, host_availability='unverified', effective_tool_mode='unknown',
        chatgpt_login_confirmed=True, argv_policy=base_args('codex.exe', disabled)[1:])


def terminal_row(directory, reservation, process, out, err, recovered=False):
    telemetry = parse_events(out, process.get('exit_code'), process.get('timeout_or_interruption', False))
    if b'model rerouted:' in err.lower():
        telemetry.update(valid=False, runtime_status='rerouted')
    elif err.strip():
        telemetry.update(valid=False, runtime_status='stderr_diagnostic')
    usage = telemetry['usage']
    if ((usage['input_tokens'] or 0) > LIMITS['input_per_stage']
        or (usage['output_tokens'] or 0) > LIMITS['output_per_stage']):
        telemetry.update(valid=False, runtime_status='token_threshold')
    answer = telemetry.pop('answer')
    body = (answer or '').encode('utf-8')
    digest = sha(body)
    relative = reservation['stage_id'] + '/candidate-' + digest + '.txt'
    path = no_links(Path(directory) / relative)
    if path.exists():
        if path.read_bytes() != body:
            raise Stop('candidate_integrity_failure')
    else:
        durable_bytes(path, body)
    try:
        candidate = strict_json(answer) if answer is not None else None
    except ValueError:
        candidate = None
    return dict(reservation, state='unresolved' if process.get('exit_code') is None else 'recorded',
        process=process, telemetry=telemetry, candidate=candidate, candidate_sha256=digest if answer is not None else None,
        candidate_artifact=relative if answer is not None else None,
        candidate_representation='received_agent_message_utf8' if answer is not None else None,
        stdout_sha256=sha(out), stderr_sha256=sha(err), recovered=recovered)


def recover(ledger):
    for row in ledger.rows():
        if row.get('imported_prior_failure'):
            continue
        target = no_links(ledger.directory / row['stage_id'])
        if row['state'] == 'recorded':
            for name, key in [('prompt.utf8.txt', 'prompt_sha256'), ('stdout.jsonl', 'stdout_sha256'),
                              ('stderr.log', 'stderr_sha256')]:
                if sha(no_links(target / name).read_bytes()) != row[key]:
                    raise Stop('receipt_integrity_failure')
            continue
        target.mkdir(exist_ok=True)
        prompt = no_links(target / 'prompt.utf8.txt')
        if not prompt.exists() or sha(prompt.read_bytes()) != row['prompt_sha256']:
            raise Stop('prompt_integrity_failure')
        process_path = no_links(target / 'process.json')
        process = strict_json(process_path.read_text(encoding='utf-8')) if process_path.exists() else dict(exit_code=None)
        chunks = []
        for name in ('stdout.jsonl', 'stderr.log'):
            path = no_links(target / name)
            chunks.append(path.read_bytes() if path.exists() else b'')
        restored = terminal_row(ledger.directory, row, process, *chunks, recovered=True)
        thread = restored['telemetry'].get('thread_id')
        if thread and any(r['telemetry'].get('thread_id') == thread for r in ledger.rows() if r['stage_id'] != row['stage_id']):
            restored['telemetry'].update(valid=False, safety_status='thread_reused')
        if restored != row:
            ledger.append('recovery', restored)


def execute_stage(exe, disabled, ledger, task, role, parent=None):
    ident = task + '-' + role + ('-a02' if role == 'E' else '-a01')
    if any(r['stage_id'] == ident for r in ledger.rows()):
        raise Stop('duplicate_invocation')
    packet = harness.packet(task) if parent is None else harness.handoff(task, parent['candidate'])
    body = json_bytes(packet)
    if len(body) > LIMITS['prompt_utf8_bytes']:
        raise Stop('prompt_byte_threshold')
    target = no_links(ledger.directory / ident)
    # Orphan pre-reservation artifacts can be reused only if exact and no spawn bytes.
    target.mkdir(exist_ok=True)
    if any((target / name).exists() for name in ('stdout.jsonl', 'stderr.log', 'process.json')):
        raise Stop('orphan_process_artifact')
    workspace = no_links(ledger.directory / 'workspaces' / ident)
    workspace.mkdir(parents=True, exist_ok=True)
    for path in (target / 'prompt.utf8.txt', workspace / 'packet.json'):
        path = no_links(path)
        if path.exists():
            if path.read_bytes() != body:
                raise Stop('prompt_integrity_failure')
        else:
            durable_bytes(path, body)
    reservation = ledger.reserve(task, role, sha(body), parent['stage_id'] if parent else None)
    argv = base_args(exe, disabled) + ['-C', str(workspace), '-m', MODELS[role], '-']
    process, out, err = capture(argv, workspace, target, body, LIMITS['seconds_per_stage'],
        on_started=lambda: ledger.append('process_started', dict(stage_id=ident, observed_at=now())))
    row = terminal_row(ledger.directory, reservation, process, out, err)
    thread = row['telemetry'].get('thread_id')
    if thread and any(r['telemetry'].get('thread_id') == thread for r in ledger.rows() if r['stage_id'] != ident):
        row['telemetry'].update(valid=False, safety_status='thread_reused')
    ledger.append('completion', row)
    return row


def sequential(ledger, call):
    """Visible-only routing. Final grader is never called in this function."""
    if any(not r.get('imported_prior_failure') and not r['telemetry']['valid'] for r in ledger.rows()):
        raise Stop('unusable_prior_attempt')
    for task in ledger.data['manifest']['plan']['task_order']:
        prior = {r['stage_id']: r for r in ledger.rows()}
        worker = prior.get(task + '-W-a01') or call(task, 'W', None)
        if not worker['telemetry']['valid']:
            raise Stop('attempt_not_usable')
        if not harness.visible(task, worker['candidate'])['pass']:
            expert = prior.get(task + '-E-a02') or call(task, 'E', worker)
            if not expert['telemetry']['valid']:
                raise Stop('attempt_not_usable')
            # E visible failure freezes; never repair or route on final correctness.


ATTEMPT_KEYS = {'attempt_id', 'task_id', 'role', 'stage', 'state', 'requested_model', 'actual_model',
    'runtime_status', 'safety_status', 'usage_status', 'usage', 'usage_observations', 'source',
    'source_sha256', 'candidate_sha256', 'candidate_representation', 'prompt_sha256',
    'stdout_sha256', 'stderr_sha256', 'exit_code', 'elapsed_seconds', 'visible_pass',
    'independently_computed_correct', 'usable'}
TASK_KEYS = {'task_id', 'planned', 'status', 'final_attempt_id', 'independently_computed_correct'}
OBS_KEYS = {'line', 'byte_offset', 'line_sha256', 'source_sha256', 'receipt_sha256', 'usage'}
STOP_CODES = {'preflight_only', 'runtime_review_required', 'limitations_ack_required', 'internal_error',
    'attempt_not_usable', 'unusable_prior_attempt', 'budget_exhausted', 'overall_token_threshold',
    'native_codex_exe_required', 'ordinary_user_chatgpt_auth_required', 'api_environment_override',
    'preflight_failed', 'cli_version_mismatch', 'required_exec_flag_missing', 'required_global_flag_missing',
    'required_tool_restriction_missing', 'interrupted_controller', 'python_3_9_required',
    'runtime_manifest_changed', 'cli_executable_mismatch', 'prior_usage_unknown', 'orphan_process_artifact',
    'attempt_outside_plan', 'invalid_takeover_parent', 'invalid_initial_parent',
    'prompt_byte_threshold', 'duplicate_invocation'}


def validate_export(result):
    required = {'schema_version', 'plan_id', 'evidence_kind', 'stop_reason', 'budget', 'physical',
                'tasks', 'attempts', 'hidden_secrecy_verified', 'actual_model_verified',
                'source_contract', 'source_hashes', 'status', 'settings'}
    def keys(value, expected):
        if type(value) is not dict or set(value) != expected:
            raise Stop('unexpected_export_field')
    keys(result, required)
    keys(result['budget'], {'cap', 'consumed', 'remaining', 'historical', 'new_reserved'})
    keys(result['physical'], {'stages', 'complete', 'unresolved_attempts', 'input_plus_output',
        'actual_model_verified', 'subscription_allowance', 'api_charge', *FIELDS,
        *(k + '_known_subtotal' for k in FIELDS)})
    keys(result['source_hashes'], {'cli_runner.py', 'harness.py', 'run-poc.ps1', 'tasks.json', 'small-test-plan.json'})
    keys(result['settings'], {'models', 'effort', 'speed', 'billing_mode', 'cli_version', 'cli_sha256'})
    keys(result['settings']['models'], {'W', 'E'})
    for hashes in result['source_hashes'].values():
        keys(hashes, {'working_tree_sha256', 'lf_sha256'})
    for task in result['tasks']:
        keys(task, TASK_KEYS)
    for attempt in result['attempts']:
        keys(attempt, ATTEMPT_KEYS); keys(attempt['usage'], set(FIELDS))
        if any(v is not None and (type(v) is not int or v < 0) for v in attempt['usage'].values()):
            raise Stop('unsafe_export_counter')
        for observation in attempt['usage_observations']:
            keys(observation, OBS_KEYS); keys(observation['usage'], set(FIELDS))
            if any(v is not None and (type(v) is not int or v < 0) for v in observation['usage'].values()):
                raise Stop('unsafe_export_counter')
    if (any(type(v) is not int or v < 0 for v in result['budget'].values())
        or result['budget']['consumed'] != len(result['attempts'])
        or result['budget']['consumed'] + result['budget']['remaining'] != 8):
        raise Stop('unsafe_export_budget')
    allowed = {'cap8-serial-public-toy-v2', 'subscription_cli_and_user_report', 'SYNTHETIC_FIXTURES',
        'initial', 'takeover', 'historical', 'reserved', 'recorded', 'unresolved', 'W', 'E', *MODELS.values(),
        'completed', 'interrupted', 'exit_unknown', 'process_failed', 'incomplete', 'capability_unavailable',
        'runtime_error', 'unknown_event', 'invalid_item', 'rerouted', 'unknown_diagnostic', 'token_threshold',
        'not_observed', 'unverified_boundary', 'tool_violation', 'thread_reused', 'stderr_diagnostic',
        'STOPPED', 'PREFLIGHT_ONLY', 'COLLECTION_COMPLETE', 'NOT_DISPATCHED', 'PARTIAL',
        'medium', 'default', 'chatgpt_subscription_requested', '0.159.2', 'unknown',
        'conflicting', 'missing', 'partial', 'reported_complete_stage', 'user_reported_partial',
        'documented_cli_runtime_event', 'user-supplied evidence', 'launch_reservation',
        'reconstructed_user_report_utf8_json', 'received_agent_message_utf8',
        'excluded_by_frozen_plan', 'not_dispatched', 'blocked_runtime', 'visible_failed', 'frozen',
        *STOP_CODES, CONTRACT}
    def check(value):
        if isinstance(value, dict):
            for item in value.values(): check(item)
        elif isinstance(value, list):
            for item in value: check(item)
        elif isinstance(value, str):
            if value not in allowed and not re.fullmatch(r'(?:[a-f0-9]{64}|P0[1-4]|legacy-P01-[WE]|P0[1-3]-[WE]-a0[12])', value):
                raise Stop('unsafe_export_value')
        elif value is not None and type(value) not in (int, float, bool):
            raise Stop('unsafe_export_type')
    check(result)
    json_bytes(result)  # Reject nonfinite numeric values.


def report(result, language):
    title, budget, limitation = (
        ('Controller checkpoint', 'Budget', 'Public toy grading; model identity and hidden secrecy unverified. Token subtotals are not subscription quota or API prices.')
        if language == 'en' else
        ('Контрольная точка controller', 'Бюджет', 'Проверка публичных toy-задач; модель и секретность grader не подтверждены. Известные суммы токенов не равны квоте подписки или цене API.'))
    b = result['budget']
    text = f'# {title}\n\n{result["evidence_kind"]}\n\n{budget}: {b["consumed"]}/{b["cap"]}; {b["remaining"]}\n\n'
    text += f'Status: {result["status"]}; {result["stop_reason"]}\n\n'
    text += '| Task | Planned | Status | Correct |\n|---|---|---|---|\n'
    for task in result['tasks']:
        text += f'| {task["task_id"]} | {task["planned"]} | {task["status"]} | {task["independently_computed_correct"]} |\n'
    text += '\n| Attempt | Runtime | Usage | Input | Output | Correct |\n|---|---|---|---|---|---|\n'
    for a in result['attempts']:
        text += f'| {a["attempt_id"]} | {a["runtime_status"]} | {a["usage_status"]} | {a["usage"]["input_tokens"]} | {a["usage"]["output_tokens"]} | {a["independently_computed_correct"]} |\n'
    return text + '\n' + limitation + '\n\n' + CONTRACT + '\n'


def safe_export(ledger, project, stop_reason=None):
    """Final grading only here; exports contain no candidate content/raw logs."""
    rows, attempts = ledger.rows(), []
    for row in rows:
        candidate = row['candidate']
        if row.get('candidate_artifact'):
            relative = row['candidate_artifact']
            expected = row['stage_id'] + '/candidate-' + row['candidate_sha256'] + '.txt'
            if relative != expected:
                raise Stop('candidate_path_invalid')
            raw = no_links(ledger.directory / relative).read_bytes()
            if sha(raw) != row['candidate_sha256']:
                raise Stop('candidate_integrity_failure')
            try: candidate = strict_json(raw.decode('utf-8'))
            except (ValueError, UnicodeError): candidate = None
            if candidate != row['candidate']:
                raise Stop('candidate_record_mismatch')
        correct = harness.grade(row['task_id'], candidate) if row['candidate_sha256'] else None
        observations = [{k: o[k] for k in OBS_KEYS} for o in row['telemetry'].get('usage_observations', [])]
        attempts.append(dict(attempt_id=row['stage_id'], task_id=row['task_id'], role=row['role'],
            stage=row['stage'], state=row['state'], requested_model=row['requested_model'], actual_model=None,
            runtime_status=row['telemetry']['runtime_status'], safety_status=row['telemetry']['safety_status'],
            usage_status=row['telemetry']['usage_status'], usage=row['telemetry']['usage'],
            usage_observations=observations, source=row['telemetry']['source'],
            source_sha256=row['telemetry'].get('source_sha256'),
            candidate_sha256=row['candidate_sha256'], candidate_representation=row.get('candidate_representation'),
            prompt_sha256=row.get('prompt_sha256'), stdout_sha256=row.get('stdout_sha256'),
            stderr_sha256=row.get('stderr_sha256'), exit_code=row['process'].get('exit_code'),
            elapsed_seconds=row['process'].get('elapsed_seconds'),
            visible_pass=harness.visible(row['task_id'], candidate)['pass'] if row['candidate_sha256'] else None,
            independently_computed_correct=correct, usable=row['telemetry']['valid']))
    tasks = []
    for task in harness.TASKS:
        current = [a for a in attempts if a['task_id'] == task and a['stage'] != 'historical']
        final = current[-1] if current else None
        tasks.append(dict(task_id=task, planned=task in ledger.data['manifest']['plan']['task_order'],
            status='excluded_by_frozen_plan' if task not in ledger.data['manifest']['plan']['task_order'] else
                   'not_dispatched' if final is None else 'blocked_runtime' if not final['usable'] else
                   'visible_failed' if not final['visible_pass'] else 'frozen',
            final_attempt_id=final['attempt_id'] if final else None,
            independently_computed_correct=final['independently_computed_correct'] if final else None))
    runtime = [e['payload'] for e in ledger.data['events'] if e['type'] == 'runtime']
    runtime = runtime[-1] if runtime else {}
    planned = [t for t in tasks if t['planned']]
    status = ('PREFLIGHT_ONLY' if stop_reason == 'preflight_only' else 'STOPPED' if stop_reason else
              'COLLECTION_COMPLETE' if all(t['status'] in ('frozen', 'visible_failed') for t in planned) else
              'NOT_DISPATCHED' if len(rows) == 2 else 'PARTIAL')
    result = dict(schema_version=2, plan_id=ledger.data['manifest']['plan']['plan_id'], status=status,
        settings=dict(models=MODELS, effort='medium', speed='default', billing_mode='chatgpt_subscription_requested',
                      cli_version=runtime.get('version', 'unknown'), cli_sha256=runtime.get('executable_sha256')),
        evidence_kind=ledger.data['manifest']['evidence_kind'], stop_reason=stop_reason,
        budget=dict(cap=8, consumed=len(rows), remaining=8-len(rows), historical=2, new_reserved=len(rows)-2),
        physical=totals(rows), tasks=tasks, attempts=attempts,
        hidden_secrecy_verified=False, actual_model_verified=False,
        source_contract=CONTRACT, source_hashes=ledger.data['manifest']['source_hashes'])
    validate_export(result)
    data = json_bytes(result)
    digest = sha(data)
    export_root = no_links(no_links(project) / 'poc-exports' / 'cap8-serial-public-toy-v2')
    snapshot = no_links(export_root / 'snapshots' / digest)
    snapshot.mkdir(parents=True, exist_ok=True)
    files = {'summary.json': data, 'report-en.md': report(result, 'en').encode('utf-8'),
             'report-ru.md': report(result, 'ru').encode('utf-8')}
    for name, body in files.items():
        path = no_links(snapshot / name)
        if path.exists():
            if path.read_bytes() != body:
                raise Stop('export_integrity_failure')
        else:
            durable_bytes(path, body)
    # Atomic pointer published last; consumers verify file hashes before use.
    pointer = dict(schema_version=2, files={name: dict(path='snapshots/' + digest + '/' + name,
                    sha256=sha(body)) for name, body in files.items()})
    durable_bytes(export_root / 'latest.json', json_bytes(pointer), replace=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', default='codex.exe')
    parser.add_argument('--data-dir', type=Path, required=True,
                        help='One persistent private cap8 directory outside this checkout; reuse on every restart')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--runtime-reviewed', action='store_true',
                        help='Prior verification of compatible authorized isolated runtime; does not install a host')
    parser.add_argument('--accept-limitations', action='store_true')
    parser.add_argument('--export-only', action='store_true', help='Replay/export without any CLI calls')
    parser.add_argument('--prior-ledger', type=Path, default=ROOT / 'failed-launches-user-ledger.json')
    args = parser.parse_args(argv)
    directory = no_links(args.data_dir)
    if directory == PROJECT or PROJECT in directory.parents:
        raise Stop('private_data_must_be_outside_project')
    if args.run and args.export_only:
        parser.error('--run and --export-only are mutually exclusive')
    reason = None
    # Bind this cap8 campaign to one data directory. A changed command-line path
    # cannot silently create another budget. Only its hash is stored in-project.
    with exclusive_lock(PROJECT / '.poc-state'), exclusive_lock(directory):
        owner = no_links(PROJECT / '.poc-state' / 'owner.json')
        identity = dict(schema_version=2, campaign='cap8-serial-public-toy-v2',
                        data_directory_sha256=sha(os.path.normcase(str(directory.resolve())).encode('utf-8')))
        if owner.exists():
            if strict_json(owner.read_text(encoding='utf-8')) != identity:
                raise Stop('data_directory_changed')
            if not (directory / 'ledger.json').exists():
                raise Stop('shared_ledger_missing')
        ledger = Ledger(directory, source_manifest(), args.prior_ledger)
        if not owner.exists():
            write_json(owner, identity)
        try:
            recover(ledger)
            if args.run and not args.runtime_reviewed:
                raise Stop('runtime_review_required')
            if args.run and not args.accept_limitations:
                raise Stop('limitations_ack_required')
            if args.run and any(not r.get('imported_prior_failure') and not r['telemetry']['valid'] for r in ledger.rows()):
                raise Stop('unusable_prior_attempt')
            if not args.export_only:
                exe, disabled, runtime = preflight(args.codex, directory)
                previous = [e['payload'] for e in ledger.data['events'] if e['type'] == 'runtime']
                if previous and previous[-1] != runtime:
                    raise Stop('runtime_manifest_changed')
                if not previous:
                    ledger.append('runtime', runtime)
                if args.run:
                    sequential(ledger, lambda task, role, parent: execute_stage(exe, disabled, ledger, task, role, parent))
                else:
                    reason = 'preflight_only'
        except Stop as e:
            reason = str(e) if str(e) in STOP_CODES else 'internal_error'
        except KeyboardInterrupt:
            reason = 'interrupted_controller'
        except Exception:
            reason = 'internal_error'
        recover(ledger)  # Salvage bytes captured before a failed terminal append.
        result = safe_export(ledger, PROJECT, reason)
        print(json.dumps(dict(stop_reason=reason, budget=result['budget'],
                             export='poc-exports/cap8-serial-public-toy-v2/latest.json')))
    return 0 if reason in (None, 'preflight_only') else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Stop, OSError, ValueError) as error:
        print('STOP: ' + (str(error) if isinstance(error, Stop) else 'ledger_or_filesystem_error'), file=sys.stderr)
        sys.exit(2)

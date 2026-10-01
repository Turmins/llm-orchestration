"""Small subscription CLI controller. Standard library only, Python >=3.9.
No execution at import. Default CLI mode is read-only preflight, not inference.
"""
import argparse
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
from datetime import datetime, timezone

import harness

ROOT = Path(__file__).resolve().parent
TASK_SHA = '9139a16cfc067e875d55f0af3bc6720d125615e9c12aa4d573c577b2de5875b4'
MODELS = {'W': 'gpt-6-luna', 'E': 'gpt-6.1-sol'}
EFFORT = 'medium'
FIELDS = ('input_tokens', 'output_tokens', 'cached_input_tokens',
          'cache_write_input_tokens', 'reasoning_output_tokens')
# Post-receipt stopping thresholds, NOT enforceable server token caps.
LIMITS = dict(stages=12, seconds_per_stage=180, input_per_stage=32000,
              output_per_stage=4000, input_overall=384000, output_overall=48000,
              prompt_utf8_bytes=16000, controller_retries=0)
DISABLE = ('shell_tool', 'unified_exec', 'apps', 'plugins', 'multi_agent',
           'multi_agent_v2', 'browser_use', 'browser_use_external',
           'browser_use_full_cdp_access', 'computer_use', 'code_mode',
           'code_mode_host', 'code_mode_only', 'view_image', 'memories',
           'hooks', 'skill_mcp_dependency_install', 'skill_search',
           'tool_suggest', 'unbounded_connection_retries')
CONTRACT = 'https://github.com/openai/codex/blob/main/codex-rs/exec/src/exec_events.rs'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    # No overwrite, including partially completed previous runs.
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def strict_json(text):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError('duplicate JSON key')
            d[k] = v
        return d
    def bad(value):
        raise ValueError('nonfinite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad)


def parse_events(data, exit_code, timed_out=False):
    """One fresh CLI thread/turn = one task stage, NOT one network request."""
    errors, events = [], []
    try:
        events = [strict_json(x) for x in data.decode('utf-8-sig').splitlines() if x.strip()]
        if any(type(e) is not dict for e in events):
            raise ValueError('non-object event')
    except (ValueError, UnicodeError) as e:
        errors.append('invalid_jsonl: ' + str(e))
        events = []
    completed = [e for e in events if e.get('type') == 'turn.completed']
    threads = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
    starts = [e for e in events if e.get('type') == 'turn.started']
    raw = completed[0].get('usage') if len(completed) == 1 else None
    usage = {k: None for k in FIELDS}
    if len(completed) != 1 or len(starts) != 1 or len(threads) != 1 or not threads[0]:
        errors.append('expected exactly one fresh thread, started turn and completed turn')
    if events and (events[0].get('type') != 'thread.started' or events[-1].get('type') != 'turn.completed'):
        errors.append('invalid fresh-turn event boundaries')
    if exit_code != 0 or timed_out:
        errors.append('process failed/interrupted; usage completeness unresolved')
    if type(raw) is not dict:
        errors.append('missing usage')
        raw = None
    else:
        for k in FIELDS:
            value = raw.get(k)
            if value is not None and (type(value) is not int or value < 0):
                errors.append('invalid counter: ' + k)
            else:
                usage[k] = value
        for k in ('input_tokens', 'output_tokens'):
            if usage[k] is None:
                errors.append('required counter unavailable: ' + k)
        for part, total in [('cached_input_tokens','input_tokens'),
                            ('cache_write_input_tokens','input_tokens'),
                            ('reasoning_output_tokens','output_tokens')]:
            if usage[part] is not None and usage[total] is not None and usage[part] > usage[total]:
                errors.append('component exceeds reported total: ' + part)
        # A default-zero receipt can be synthesized by CLI when usage is missing.
        if usage['input_tokens'] == 0:
            errors.append('zero input cannot establish measured inference for a nonempty prompt')
    answers, item_errors = [], []
    allowed_items = {'agent_message', 'reasoning'}
    allowed_events = {'thread.started', 'turn.started', 'turn.completed',
                      'item.started', 'item.updated', 'item.completed'}
    for e in events:
        kind = e.get('type')
        if kind not in allowed_events:
            errors.append('error or unsupported event: ' + str(kind))
        if str(kind).startswith('item.'):
            item = e.get('item', {})
            if type(item) is not dict:
                errors.append('invalid item'); continue
            if item.get('type') not in allowed_items:
                errors.append('tool/error/unsupported item: ' + str(item.get('type')))
            if item.get('type') == 'error':
                item_errors.append(str(item.get('message', '')))
            if kind == 'item.completed' and item.get('type') == 'agent_message':
                answers.append(item.get('text'))
    if not answers or not isinstance(answers[-1], str):
        errors.append('missing final agent message')
    # Reroute is emitted as item.error by current public source. Absence is NOT proof.
    reroutes = [x for x in item_errors if 'model rerouted:' in x.lower()]
    return dict(valid=not errors, errors=errors, usage=usage, raw_usage=raw,
                thread_id=threads[0] if len(threads) == 1 else None,
                turn_id=None, request_id=None, response_id=None, actual_model=None,
                model_attribution='UNVERIFIED', rerouted=True if reroutes else None,
                reroute_evidence=reroutes, answer=answers[-1] if answers else None,
                scope='fresh_thread_single_turn_stage', network_request_count=None,
                source='documented_cli_runtime_event', source_contract_ref=CONTRACT)


def totals(rows):
    unique = {}
    for r in rows:
        key = r['stage_id']
        if key in unique and unique[key] != r:
            raise ValueError('conflicting stage replay')
        unique[key] = r
    rows = list(unique.values())
    result = {'stages': len(rows), 'complete': all(r['telemetry']['valid'] for r in rows)}
    for k in FIELDS:
        xs = [r['telemetry']['usage'][k] for r in rows]
        result[k] = sum(xs) if result['complete'] and all(x is not None for x in xs) else None
        result[k + '_known_subtotal'] = sum(x for x in xs if x is not None)
    # Components are never added to these totals; cache disjointness is not assumed.
    result['input_plus_output'] = (result['input_tokens'] + result['output_tokens']
        if result['complete'] and result['input_tokens'] is not None and result['output_tokens'] is not None else None)
    result['actual_model_verified'] = False
    result['subscription_allowance'] = None
    result['api_charge'] = None
    return result


def capture(argv, cwd, target, prompt=None, timeout=30):
    target.mkdir()
    started, stamp = time.monotonic(), now()
    code, timed_out, launch_error = None, False, None
    with (target/'stdout.jsonl').open('xb') as out, (target/'stderr.log').open('xb') as err:
        try:
            # Byte stdin/stdout avoid PS5.1 ANSI/UTF-16 and quoting differences.
            proc = subprocess.Popen(argv, cwd=str(cwd), stdin=subprocess.PIPE,
                                    stdout=out, stderr=err, shell=False)
            try:
                proc.communicate(input=prompt, timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                timed_out = True
                proc.kill()
                proc.wait()
                # Killing the client does not prove server cancellation or zero usage.
            code = proc.returncode
        except OSError as e:
            launch_error = str(e)
    result = dict(argv=argv, started_at=stamp, ended_at=now(),
                  elapsed_seconds=time.monotonic()-started, exit_code=code,
                  timeout_or_interruption=timed_out, launch_error=launch_error)
    write_json(target/'process.json', result)
    return result, (target/'stdout.jsonl').read_bytes(), (target/'stderr.log').read_bytes()


def base_args(exe, disabled):
    args = [exe, '--ask-for-approval', 'never', 'exec', '--json', '--ephemeral',
            '--ignore-user-config', '--skip-git-repo-check', '--sandbox', 'read-only']
    settings = ['forced_login_method="chatgpt"', 'model_provider="openai"',
                'model_reasoning_effort="medium"', 'service_tier="default"',
                'web_search="disabled"', 'project_doc_max_bytes=0',
                'agents.enabled=false']
    for s in settings:
        args += ['-c', s]
    for feature in disabled:
        args += ['--disable', feature]
    return args


def preflight(exe, run):
    if sys.version_info < (3, 9):
        raise ValueError('Existing Python >=3.9 required; no installer is used')
    if sha((ROOT/'tasks.json').read_bytes()) != TASK_SHA:
        raise ValueError('Frozen task bytes changed')
    # Never inspect values or credentials. Ambiguous API/provider overrides stop.
    if any(os.environ.get(k) for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')):
        raise ValueError('API/provider environment override is present; use your ordinary ChatGPT terminal')
    found = shutil.which(exe)
    if not found or Path(found).suffix.lower() != '.exe':
        raise ValueError('Pass an existing native codex.exe, not a shell/cmd wrapper')
    texts = {}
    for name, tail in [('version',['--version']),('help',['--help']),
                       ('exec-help',['exec','--help']),('login',['login','status']),
                       ('features',['features','list'])]:
        result, out, err = capture([found]+tail, run, run/('preflight-'+name))
        if result['exit_code'] != 0:
            raise ValueError('Preflight failed: ' + name)
        texts[name] = (out+err).decode('utf-8', errors='replace')
    if not re.search(r'codex-cli\s+0\.159\.2(?:\s|$)', texts['version']):
        raise ValueError('This adapter targets user-tested CLI 0.159.2; review contract before changing versions')
    if 'Logged in using ChatGPT' not in texts['login']:
        raise ValueError('ChatGPT login not confirmed; no login/auth changes will be made')
    for flag in ('--json','--model','--ephemeral','--ignore-user-config','--skip-git-repo-check','--sandbox'):
        if flag not in texts['exec-help']:
            raise ValueError('Required installed exec flag absent: ' + flag)
    for flag in ('--ask-for-approval','--disable'):
        if flag not in texts['help']:
            raise ValueError('Required installed global flag absent: ' + flag)
    features = {line.split()[0] for line in texts['features'].splitlines() if line.strip()}
    mandatory = {'shell_tool','unified_exec','apps','plugins','multi_agent'}
    if not mandatory <= features:
        raise ValueError('Required tool-disable features absent from installed feature list')
    disabled = [x for x in DISABLE if x in features]
    info = dict(version=texts['version'].strip(), executable_sha256=sha(Path(found).read_bytes()),
                chatgpt_login_confirmed=True, requested_models=MODELS,
                model_catalog_source='https://learn.chatgpt.com/docs/models',
                model_availability='unverified: no documented non-inference models-list subcommand in reviewed CLI',
                actual_model=None, model_attribution='UNVERIFIED', disabled_features=disabled,
                isolation='best effort; read-only is not a read-visibility jail',
                token_limits='post-receipt stopping thresholds, not hard server limits', limits=LIMITS,
                transport_retries='not controllable via built-in provider overrides; stage usage only',
                forced_login_method='chatgpt', source_contract=CONTRACT)
    write_json(run/'preflight.json', info)
    return found, disabled


def execute_stage(exe, disabled, run, rows, task, role, stage, logical, parent=None, forced=False):
    if len(rows) >= (2 if forced else LIMITS['stages']):
        raise ValueError('Stage budget exhausted')
    if rows:
        total = totals(rows)
        if not total['complete'] or total['input_tokens'] >= LIMITS['input_overall'] or total['output_tokens'] >= LIMITS['output_overall']:
            raise ValueError('Usage unresolved or stopping threshold reached')
    ident = task+'-'+role+'-'+stage
    workspace = Path(tempfile.mkdtemp(prefix='toy-poc-task-'))
    # This directory contains no repo, references, tests, receipts or candidates.
    if parent is None:
        packet = harness.packet(task)
    else:
        packet = harness.handoff(task, parent['candidate'], forced=forced)
    body = (json.dumps(packet, ensure_ascii=False)+'\n').encode('utf-8')
    if len(body) > LIMITS['prompt_utf8_bytes']:
        raise ValueError('Prompt byte ceiling exceeded')
    target = run/ident
    argv = base_args(exe, disabled)+['-C',str(workspace),'-m',MODELS[role],'-']
    result, out, err = capture(argv, workspace, target, body, LIMITS['seconds_per_stage'])
    (target/'prompt.utf8.txt').write_bytes(body)
    parsed = parse_events(out, result['exit_code'], result['timeout_or_interruption'])
    candidate = None
    if isinstance(parsed['answer'], str):
        try:
            candidate = strict_json(parsed['answer'])
        except ValueError:
            pass  # Malformed model JSON is visible failure, not hidden feedback.
    # Always freeze raw answer bytes, even malformed ones; never execute model code.
    answer_bytes = (parsed['answer'] or '').encode('utf-8')
    (target/'candidate.txt').write_bytes(answer_bytes)
    usage = parsed['usage']
    if 'model rerouted:' in err.decode('utf-8', errors='replace').lower():
        parsed['valid'] = False
        parsed['rerouted'] = True
        parsed['errors'].append('reroute reported on stderr; see private raw log')
    if any(r['telemetry']['thread_id'] == parsed['thread_id'] for r in rows):
        parsed['valid'] = False
        parsed['errors'].append('thread ID reused across stages')
    if parsed['valid'] and (usage['input_tokens'] > LIMITS['input_per_stage'] or usage['output_tokens'] > LIMITS['output_per_stage']):
        parsed['valid'] = False
        parsed['errors'].append('post-receipt stage token threshold exceeded')
    row = dict(stage_id=ident, task_id=task, role=role,
               strategy='forced-technical' if forced else ('shared-W-initial' if role=='W' else logical[0]),
               logical_strategies=logical, attempt=2 if parent else 1, stage=stage,
               parent_stage_id=parent['stage_id'] if parent else None,
               requested_model=MODELS[role], requested_effort=EFFORT, actual_model=None,
               actual_effort=None, requested_speed='default', actual_speed=None,
               billing_mode='chatgpt_subscription_requested', forced_technical=forced,
               process=result, telemetry=parsed, candidate=candidate,
               candidate_sha256=sha(answer_bytes), stdout_sha256=sha(out), stderr_sha256=sha(err),
               raw_usage_sha256=sha(json.dumps(parsed['raw_usage'],sort_keys=True,separators=(',',':')).encode()) if parsed['raw_usage'] is not None else None)
    rows.append(row)
    write_json(target/'record.json', row)
    with (run/'ledger.jsonl').open('a', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
    print(ident+': '+('receipt parsed; actual model UNVERIFIED' if parsed['valid'] else 'STOP: '+'; '.join(parsed['errors'])), flush=True)
    if not parsed['valid']:
        raise ValueError('Stage failed telemetry/isolation/runtime gate; no retry or escalation')
    return row


def comparison(call, selected=None):
    """Only visible routing here. Grader is invoked later after all answers freeze."""
    selected = {} if selected is None else selected
    for i, task in enumerate(harness.TASKS):
        pair = {}
        for role in (('W','E') if i % 2 == 0 else ('E','W')):
            logical = ['W-only','W-to-E'] if role=='W' else ['E-only']
            pair[role] = call(task,role,'initial',logical)
        w, e = pair['W'], pair['E']
        final = w
        if not harness.visible(task,w['candidate'])['pass']:
            final = call(task,'E','takeover',['W-to-E'],parent=w)
        selected[task] = {'W-only':w,'E-only':e,'W-to-E':final}
    return selected


def finish(run, rows, selected, error, forced):
    # The sole hidden acceptance invocation is here, after collection has ended.
    frozen = {r['stage_id']:r['candidate_sha256'] for r in rows}
    write_json(run/'frozen-candidates.json',frozen)
    for r in rows:
        if sha((run/r['stage_id']/'candidate.txt').read_bytes()) != r['candidate_sha256']:
            raise ValueError('Candidate changed before acceptance')
    acceptance = {}
    if not error:
        for task, policies in selected.items():
            acceptance[task] = {p:dict(stage_id=r['stage_id'],
                visible_pass=harness.visible(task,r['candidate'])['pass'],
                independently_computed_acceptance=harness.grade(task,r['candidate'])) for p,r in policies.items()}
    summary = dict(status='STOPPED_INCOMPLETE' if error else 'COMPLETED_UNVERIFIED_MODEL_AND_ISOLATION',
        error=error, kind='forced_technical_excluded_from_comparison' if forced else 'four_original_toy_tasks',
        actual_model_verified=False, grader_access_isolation_verified=False,
        physical=totals(rows), logical={}, acceptance=acceptance,
        paired_task_count=len(selected), missing_tasks=[t for t in harness.TASKS if t not in selected],
        subscription_savings=None, api_cost=None, limitations=[
            'Requested aliases do not prove actual models; no confirmed economic ranking.',
            'CLI stage aggregates accepted; per-network-request receipts are not required.',
            'Shared W initial is correlated policy replay, not an independent W-to-E trial.',
            'Raw logs are private; no automatic publication. Client timeout does not prove server cancellation.',
            'No price/quota conversion; incomplete rows remain in ledger and known subtotals.'])
    if not forced:
        for policy in ('W-only','E-only','W-to-E'):
            summary['logical'][policy] = totals([r for r in rows if policy in r['logical_strategies']])
    write_json(run/'summary.json',summary)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codex',default='codex.exe')
    p.add_argument('--run',action='store_true')
    p.add_argument('--accept-limitations',action='store_true')
    p.add_argument('--forced-handoff-only',action='store_true')
    a = p.parse_args()
    # Outside checkout; never copied to the agent workspace and never git-added.
    run = Path(tempfile.mkdtemp(prefix='toy-poc-run-'))
    print('Private run directory: '+str(run), flush=True)
    rows, selected, error = [], {}, None
    try:
        exe, disabled = preflight(a.codex,run)
        print('WARNING: actual model cannot be confirmed by this CLI adapter. Read-only is not full read isolation. Token thresholds are post-receipt. Included quota/credits are not measurable; verify your subscription has included capacity before running.',flush=True)
        if not a.run:
            print('Preflight only: no model calls. Add -Run -AcceptUnverifiedModelAndIsolation to the PowerShell command for the bounded diagnostic.',flush=True)
            return 0
        if not a.accept_limitations:
            raise ValueError('Explicit -AcceptUnverifiedModelAndIsolation required for this unverified diagnostic')
        def call(task,role,stage,logical,parent=None):
            return execute_stage(exe,disabled,run,rows,task,role,stage,logical,parent,a.forced_handoff_only)
        write_json(run/'plan.json',dict(task_sha256=TASK_SHA,task_order=list(harness.TASKS),models=MODELS,
                   effort=EFFORT,limits=LIMITS,forced_handoff_only=a.forced_handoff_only,created=now()))
        if a.forced_handoff_only:
            w=call('P03','W','initial',[])
            e=call('P03','E','takeover',[],w)
            selected={'P03':{'forced-technical':e}}
        else:
            comparison(call, selected)
    except (Exception,KeyboardInterrupt) as e:
        error=type(e).__name__+': '+str(e)
        print('STOP: '+error,flush=True)
    if a.run:
        finish(run,rows,selected,error,a.forced_handoff_only)
    elif error:
        write_json(run/'preflight-failure.json',dict(error=error))
    return 2 if error else 0


if __name__=='__main__':
    sys.exit(main())

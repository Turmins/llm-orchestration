"""Offline receipt validation only. No model, network, credential or runtime access."""
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SCHEMA = json.loads((ROOT / 'usage.schema.json').read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def normalize(row, allow_synthetic=False):
    """Return totals and disjoint price buckets; raise if required attribution is absent."""
    VALIDATOR.validate(row)
    synthetic = row['record_kind'] == 'synthetic' and row['source'] == 'synthetic'
    if synthetic and not allow_synthetic:
        raise ValueError('Synthetic receipts cannot pass a real measurement gate')
    if not synthetic and (row['record_kind'] != 'observed' or row['source'] not in ['server_usage', 'documented_runtime_event']):
        raise ValueError('No authoritative receipt source')
    if row['receipt_status'] != 'final' or row['scope'] not in ['request', 'turn'] or row['billable_calls_in_scope'] != 1:
        raise ValueError('Not a final single-call receipt; cumulative/account totals are inadmissible')
    for key in ['request_id', 'confirmed_model', 'model_evidence_ref', 'source_contract_ref', 'input_tokens', 'output_tokens', 'raw_usage', 'raw_usage_sha256']:
        if row[key] is None:
            raise ValueError('Required field unavailable: ' + key)
    if not row['event_ids'] or row['raw_usage_sha256'] != digest(row['raw_usage']):
        raise ValueError('Missing event provenance or changed safe raw usage')
    for field, path in row['usage_field_paths'].items():
        if path is None:
            if row[field] is not None:
                raise ValueError('Numeric field lacks a raw source path: ' + field)
            continue
        value = row['raw_usage']
        try:
            for part in path.lstrip('/').split('/'):
                value = value[part.replace('~1', '/').replace('~0', '~')]
        except (KeyError, TypeError):
            raise ValueError('Raw usage path does not resolve: ' + field)
        if type(value) is not type(row[field]) or value != row[field]:
            raise ValueError('Normalized field differs from raw source: ' + field)
    if row['confirmed_model'] != row['requested_model'] or row['rerouted'] is not False:
        raise ValueError('Model mismatch, reroute or unresolved routing: stop frozen-policy comparison')
    i, o = row['input_tokens'], row['output_tokens']
    cr, cw, reason = row['cache_read_tokens'], row['cache_write_tokens'], row['reasoning_output_tokens']
    if row['input_semantics'] == 'excludes_cache':
        if cr is None or cw is None or row['cache_categories_disjoint'] is not True:
            raise ValueError('Cannot reconstruct total input')
        uncached = i
        i += cr + cw
    elif row['input_semantics'] == 'includes_cache':
        if any(x is not None and x > i for x in [cr, cw]):
            raise ValueError('Cache category exceeds inclusive input')
        uncached = i - cr - cw if cr is not None and cw is not None and row['cache_categories_disjoint'] is True else None
        if uncached is not None and uncached < 0:
            raise ValueError('Cache categories exceed inclusive input')
    else:
        raise ValueError('Unknown input semantics')
    if row['output_semantics'] == 'excludes_reasoning':
        if reason is None:
            raise ValueError('Cannot reconstruct total output')
        o += reason
    elif row['output_semantics'] == 'includes_reasoning':
        if reason is not None and reason > o:
            raise ValueError('Reasoning exceeds inclusive output')
    else:
        raise ValueError('Unknown output semantics')
    if row['total_tokens'] is not None and row['total_tokens'] != i + o:
        raise ValueError('Reported total inconsistent with documented normalized semantics')
    return {'input_total': i, 'output_total': o, 'uncached_input': uncached,
            'cache_read': cr, 'cache_write': cw}


def aggregate(rows, allow_synthetic=False):
    """Deduplicate exact receipt replay, reject conflicts and reused server request IDs."""
    seen, requests = {}, {}
    physical = {'input_total': 0, 'output_total': 0, 'calls': 0}
    logical = {}
    for row in rows:
        n = normalize(row, allow_synthetic=allow_synthetic)
        key = row['physical_call_id']
        if key in seen:
            if seen[key] != row:
                raise ValueError('Conflicting final receipts for one physical call')
            continue
        if row['request_id'] in requests and requests[row['request_id']] != key:
            raise ValueError('One server request assigned multiple physical IDs')
        seen[key] = row
        requests[row['request_id']] = key
        for bucket in [physical] + [logical.setdefault(s, {'input_total': 0, 'output_total': 0, 'calls': 0}) for s in row['logical_strategies']]:
            bucket['input_total'] += n['input_total']
            bucket['output_total'] += n['output_total']
            bucket['calls'] += 1
    return {'physical': physical, 'logical': logical}


def api_token_estimate(normalized, rates):
    """Hypothetical token tariff only, never an actual charge or subscription quota."""
    fields = ['uncached_input', 'cache_read', 'cache_write', 'output_total']
    if any(normalized[k] is None for k in fields):
        return None
    return sum(Decimal(normalized[k]) * Decimal(str(rates[k])) for k in fields) / Decimal(1000000)


def visible_decision(*, infrastructure_ok, telemetry_ok, scope_ok, snapshot_recoverable,
                     candidate_present, public_baseline_valid, public_regression,
                     checks_completed, attempts_used):
    """Synthetic decision-table helper; deliberately has no hidden-grader argument."""
    if not all([infrastructure_ok, telemetry_ok, scope_ok, snapshot_recoverable, public_baseline_valid]):
        return 'stop_infrastructure_or_gate'
    if not checks_completed:
        return 'unresolved_check_timeout'
    if candidate_present and not public_regression:
        return 'freeze_operational_candidate'
    return 'one_visible_evidence_intervention' if attempts_used == 1 else 'unresolved'

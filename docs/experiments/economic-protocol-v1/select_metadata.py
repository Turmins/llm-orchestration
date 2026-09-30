"""Offline deterministic selection from an already authorized metadata-only export.
No fetching, inference, container operations, or reading dataset patches.
CLI: python select_metadata.py allowed-metadata.json output-manifest.json
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / 'protocol.json').read_text())['selection']
FIELDS = {'instance_id', 'repository_group', 'repo', 'base_commit', 'created_at', 'issue_key',
          'problem_sha256', 'docker_image', 'image_digest', 'repository_license'}
HEAD = {'dataset_revision', 'harbor_revision', 'harness_revision', 'rows'}


def rank(seed, kind, value):
    return hashlib.sha256((seed + '\0' + kind + '\0' + value).encode()).digest()


def select(data, seed=PLAN['seed'], calibration_n=10, eval_n=50):
    if set(data) != HEAD:
        raise ValueError('Require exact metadata envelope; never pass a full dataset export')
    if not re.fullmatch('[a-f0-9]{40,64}', data['dataset_revision'] or ''):
        raise ValueError('Immutable dataset commit required')
    for key in ['harbor_revision', 'harness_revision']:
        if not data[key] or data[key] in ['main', 'latest']:
            raise ValueError('Immutable revision required: ' + key)
    excluded = set(json.loads((ROOT / 'manifest.json').read_text())['prior_exposure_exclusions'])
    unique, audits = {}, []
    for row in data['rows']:
        if set(row) != FIELDS:
            raise ValueError('Metadata allowlist violation: patch/content or required field mismatch')
        if not all(isinstance(row[k], str) and row[k] for k in FIELDS - {'image_digest'}):
            raise ValueError('Incomplete metadata')
        if not re.fullmatch('[a-f0-9]{40,64}', row['base_commit']) or not re.fullmatch('[a-f0-9]{64}', row['problem_sha256']):
            raise ValueError('Bad commit/fingerprint')
        if row['image_digest'] is not None and not re.fullmatch('sha256:[a-f0-9]{64}', row['image_digest']):
            raise ValueError('Bad image digest')
        datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
        ident = row['instance_id']
        if ident in unique and unique[ident] != row:
            raise ValueError('Conflicting duplicate instance ID')
        if ident in unique:
            audits.append({'id': ident, 'reason': 'identical_id_replay'})
        unique[ident] = row
    # Connected duplicate groups, independent of input order. Same problem hash or
    # same repo/issue collapses even if another alias connects the groups transitively.
    rows = sorted(unique.values(), key=lambda x: x['instance_id'])
    parents = list(range(len(rows)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    keys = {}
    for i, row in enumerate(rows):
        for key in [('problem', row['problem_sha256']), ('issue', row['repo'].casefold(), row['issue_key'])]:
            if key in keys:
                a, b = find(i), find(keys[key]);parents[max(a,b)] = min(a,b)
            else:
                keys[key] = i
    groups = {}
    for i, row in enumerate(rows):groups.setdefault(find(i), []).append(row)
    eligible = []
    for group in groups.values():
        blocked = any(x['instance_id'] in excluded for x in group)
        for row in group:
            if blocked or row != group[0]:
                audits.append({'id': row['instance_id'], 'reason': 'prior_exposure_group' if blocked else 'duplicate_problem_or_issue'})
        row = group[0]
        if blocked:continue
        if not row['created_at'].startswith(PLAN['month'] + '-'):
            audits.append({'id': row['instance_id'], 'reason': 'outside_pinned_month'});continue
        eligible.append(row)
    pools = {'calibration': [], 'eval': []}
    for row in eligible:
        bucket = int.from_bytes(rank(seed, 'group', row['repository_group'].casefold())[:8], 'big') % 5
        pools['calibration' if bucket == 0 else 'eval'].append(row)
    for values in pools.values():values.sort(key=lambda row: (rank(seed, 'task', row['instance_id']), row['instance_id']))
    if len(pools['calibration']) < calibration_n or len(pools['eval']) < eval_n:
        raise ValueError('Insufficient fixed pools; do not change seed/month or relax separation after looking')
    cal, ev = pools['calibration'][:calibration_n], pools['eval'][:eval_n]
    assert not ({x['repository_group'].casefold() for x in cal} & {x['repository_group'].casefold() for x in ev})
    return {'status':'SELECTED_NOT_RUNNABLE_PENDING_GATES','runnable':False,'seed':seed,
            'dataset_revision':data['dataset_revision'],'harbor_revision':data['harbor_revision'],
            'harness_revision':data['harness_revision'],'calibration':cal,'eval':ev,
            'metadata_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'duplicate_audit':audits,'split_audit':{'disjoint_ids':True,'disjoint_repository_groups':True},
            'image_digest_fields_complete':all(x['image_digest'] is not None for x in cal+ev),
            'image_digests_verified':False}

if __name__ == '__main__':
    data=json.loads(Path(sys.argv[1]).read_text())
    result=select(data)
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')

"""Synthetic offline tests only: no real usage or benchmark results are generated."""
import copy
import json
import unittest
from pathlib import Path
from decimal import Decimal
from jsonschema import Draft202012Validator
from accounting import SCHEMA, digest, normalize, aggregate, api_token_estimate, visible_decision
from select_metadata import select, rank, PLAN

ROOT=Path(__file__).resolve().parent


def receipt():
    row={k:None for k in SCHEMA['required']}
    row.update(schema_version='1.0',record_kind='synthetic',record_id='SYNTHETIC-record-1',
      physical_call_id='SYNTHETIC-call-1',experiment_id='SYNTHETIC-only',task_id='SYNTHETIC-task',
      split='synthetic',strategy='shared-W-initial',logical_strategies=['W-only','W-to-E'],
      stage='initial',attempt=1,request_id='SYNTHETIC-request-1',response_id='SYNTHETIC-response-1',
      requested_model='SYNTHETIC-model',confirmed_model='SYNTHETIC-model',
      model_evidence_ref='SYNTHETIC-model-event',rerouted=False,status='completed',receipt_status='final',
      source='synthetic',scope='request',billable_calls_in_scope=1,source_contract_ref='SYNTHETIC-semantics-v1',
      event_ids=['SYNTHETIC-event-1'],input_tokens=1000,output_tokens=200,cache_read_tokens=300,
      cache_write_tokens=100,reasoning_output_tokens=80,total_tokens=1200,input_semantics='includes_cache',
      output_semantics='includes_reasoning',cache_categories_disjoint=True,availability_notes=[],billing_mode='synthetic',
      raw_usage={'input_tokens':1000,'input_tokens_details':{'cached_tokens':300,'cache_write_tokens':100},
                 'output_tokens':200,'output_tokens_details':{'reasoning_tokens':80},'total_tokens':1200},
      usage_field_paths={'input_tokens':'/input_tokens','output_tokens':'/output_tokens','cache_read_tokens':'/input_tokens_details/cached_tokens','cache_write_tokens':'/input_tokens_details/cache_write_tokens','reasoning_output_tokens':'/output_tokens_details/reasoning_tokens','total_tokens':'/total_tokens'})
    row['raw_usage_sha256']=digest(row['raw_usage'])
    return row


def metadata():
    rows=[]
    for split in ['calibration','eval']:
        for i in range(60):
            j=0
            while True:
                group=f'SYNTHETIC-{split}-{i}-{j}'
                iscal=int.from_bytes(rank(PLAN['seed'],'group',group.casefold())[:8],'big')%5==0
                if iscal==(split=='calibration'):break
                j+=1
            ident=f'SYNTHETIC-{split}-{i:03}'
            rows.append({'instance_id':ident,'repository_group':group,'repo':group+'/repo',
              'base_commit':'a'*40,'created_at':'2026-07-15T00:00:00Z','issue_key':f'issue-{i}',
              'problem_sha256':digest(ident),'docker_image':'SYNTHETIC/no-image','image_digest':None,
              'repository_license':'SYNTHETIC-not-a-license'})
    return {'dataset_revision':'b'*40,'harbor_revision':'SYNTHETIC-revision','harness_revision':'SYNTHETIC-revision','rows':rows}


class PreparationTests(unittest.TestCase):
    def test_schema(self):
        Draft202012Validator.check_schema(SCHEMA)
        Draft202012Validator(SCHEMA).validate(receipt())
    def test_synthetic_never_real_gate(self):
        with self.assertRaises(ValueError):normalize(receipt())
    def test_inclusive_cache_and_reasoning(self):
        n=normalize(receipt(),True)
        self.assertEqual(n,dict(input_total=1000,output_total=200,uncached_input=600,cache_read=300,cache_write=100))
        rates=dict(uncached_input=2,cache_read=.1,cache_write=2.5,output_total=10)
        self.assertEqual(api_token_estimate(n,rates),Decimal('.00348'))
    def test_exclusive_semantics(self):
        r=receipt();r.update(input_tokens=600,output_tokens=120,input_semantics='excludes_cache',output_semantics='excludes_reasoning')
        r['raw_usage']['input_tokens']=600;r['raw_usage']['output_tokens']=120;r['raw_usage_sha256']=digest(r['raw_usage'])
        self.assertEqual(normalize(r,True)['input_total'],1000)
        self.assertEqual(normalize(r,True)['output_total'],200)
    def test_cache_unavailable_not_zero(self):
        r=receipt();r['cache_write_tokens']=None;r['usage_field_paths']['cache_write_tokens']=None;r['raw_usage']['input_tokens_details'].pop('cache_write_tokens');r['raw_usage_sha256']=digest(r['raw_usage'])
        n=normalize(r,True);self.assertIsNone(n['uncached_input']);self.assertEqual(n['input_total'],1000)
        self.assertIsNone(api_token_estimate(n,{}))
    def test_required_absence_scope_and_reroute(self):
        for change in [dict(input_tokens=None),dict(output_tokens=None),dict(confirmed_model=None),dict(request_id=None),
                       dict(scope='account'),dict(scope='turn',billable_calls_in_scope=2),dict(receipt_status='provisional'),
                       dict(rerouted=True),dict(confirmed_model='other'),dict(input_semantics='unknown')]:
            r=receipt();r.update(change)
            with self.assertRaises(ValueError):normalize(r,True)
    def test_invalid_buckets_totals_and_raw(self):
        for change in [dict(cache_write_tokens=800),dict(reasoning_output_tokens=201),dict(total_tokens=999),dict(raw_usage_sha256='0'*64)]:
            r=receipt();r.update(change)
            if 'raw_usage_sha256' not in change:
                for field in change:
                    node=r['raw_usage'];parts=r['usage_field_paths'][field].strip('/').split('/')
                    for part in parts[:-1]:node=node[part]
                    node[parts[-1]]=r[field]
                r['raw_usage_sha256']=digest(r['raw_usage'])
            with self.assertRaises(ValueError):normalize(r,True)
    def test_raw_mapping_mismatch(self):
        r=receipt();r['input_tokens']=900
        with self.assertRaises(ValueError):normalize(r,True)
    def test_physical_dedup_and_logical_shared(self):
        r=receipt();a=aggregate([r,copy.deepcopy(r)],True)
        self.assertEqual(a['physical']['calls'],1)
        self.assertEqual(a['logical']['W-only']['input_total'],1000)
        self.assertEqual(a['logical']['W-to-E']['input_total'],1000)
    def test_failure_included_and_conflicts_rejected(self):
        r=receipt();other=copy.deepcopy(r);other.update(record_id='SYNTHETIC-record-2',physical_call_id='SYNTHETIC-call-2',request_id='SYNTHETIC-request-2',status='failed',stage='repair',attempt=2,strategy='W-only',logical_strategies=['W-only'])
        self.assertEqual(aggregate([r,other],True)['physical']['calls'],2)
        other['physical_call_id']=r['physical_call_id']
        with self.assertRaises(ValueError):aggregate([r,other],True)
    def test_reused_request_rejected(self):
        r=receipt();other=copy.deepcopy(r);other['physical_call_id']='SYNTHETIC-different'
        with self.assertRaises(ValueError):aggregate([r,other],True)
    def test_visible_routing(self):
        args=dict(infrastructure_ok=True,telemetry_ok=True,scope_ok=True,snapshot_recoverable=True,candidate_present=True,public_baseline_valid=True,public_regression=False,checks_completed=True,attempts_used=1)
        self.assertEqual(visible_decision(**args),'freeze_operational_candidate')
        args['public_regression']=True;self.assertEqual(visible_decision(**args),'one_visible_evidence_intervention')
        args['attempts_used']=2;self.assertEqual(visible_decision(**args),'unresolved')
        args['telemetry_ok']=False;self.assertEqual(visible_decision(**args),'stop_infrastructure_or_gate')
    def test_deterministic_disjoint_selection(self):
        d=metadata();a=select(d);d['rows'].reverse();b=select(d)
        self.assertEqual(a['calibration'],b['calibration']);self.assertEqual(a['eval'],b['eval'])
        self.assertEqual((len(a['calibration']),len(a['eval'])),(10,50))
        self.assertTrue(a['split_audit']['disjoint_repository_groups']);self.assertFalse(a['runnable'])
    def test_duplicates_and_content_refused(self):
        d=metadata();d['rows'].append(copy.deepcopy(d['rows'][0]));self.assertTrue(select(d)['duplicate_audit'])
        d['rows'][-1]['base_commit']='c'*40
        with self.assertRaises(ValueError):select(d)
        d=metadata();d['rows'][0]['patch']='SYNTHETIC forbidden field'
        with self.assertRaises(ValueError):select(d)
    def test_fingerprint_alias_collapses(self):
        d=metadata();alias=copy.deepcopy(d['rows'][0]);alias['instance_id']='ZZ-SYNTHETIC-alias';alias['repository_group']='different';d['rows'].append(alias)
        a=select(d);self.assertTrue(any(x['reason']=='duplicate_problem_or_issue' for x in a['duplicate_audit']))
    def test_unpinned_or_insufficient_pool_refused(self):
        d=metadata();d['dataset_revision']='main'
        with self.assertRaises(ValueError):select(d)
        d=metadata();d['rows']=d['rows'][:2]
        with self.assertRaises(ValueError):select(d)
    def test_plan_budget_and_manifest_closed(self):
        p=json.loads((ROOT/'protocol.json').read_text());b=p['budget_plan_only']
        self.assertEqual(2*Decimal('.0225')+3*Decimal('.45'),Decimal(str(b['api_task_usd_upper'])))
        self.assertEqual(60*Decimal('1.395')+Decimal('.4725'),Decimal(str(b['total_60_tasks_and_probes_usd_upper'])))
        self.assertFalse(json.loads((ROOT/'manifest.json').read_text())['runnable'])

if __name__=='__main__':unittest.main(verbosity=2)

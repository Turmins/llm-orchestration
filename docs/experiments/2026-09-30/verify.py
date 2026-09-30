"""Offline checker. Never invokes a model or network. Exit nonzero on any error."""
from pathlib import Path
import json,sys,copy,time
ROOT=Path(__file__).resolve().parent

def load(path):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('duplicate key')
   d[k]=v
  return d
 return json.loads(Path(path).read_text(),object_pairs_hook=pairs)

def same(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(same(a[k],v) for k,v in b.items())
 if isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b

def check(candidate,expected):
 if type(candidate)!=dict or candidate.keys()!=expected.keys():return {'envelope':False}
 return {k:same(candidate[k],v) for k,v in expected.items()}

if __name__=='__main__':
 t=time.perf_counter();gold=load(ROOT/'expected.json')
 # Acceptance gate mutation check: a wrong required answer must be rejected.
 bad=copy.deepcopy(gold);bad['T1']['peak']+=1
 assert check(bad,gold)['T1'] is False
 # Positive self-assessment cannot override the envelope or a required failure.
 bad['approved']=True
 assert check(bad,gold)=={'envelope':False}
 results={}
 for name in sys.argv[1:]:
  try:results[Path(name).name]=check(load(name),gold)
  except (ValueError,OSError) as e:results[Path(name).name]={'parse':False}
 print(json.dumps({'checks':results,'mutation_gate':'PASS','elapsed_seconds':time.perf_counter()-t},indent=2))
 sys.exit(not all(all(x.values()) for x in results.values()))

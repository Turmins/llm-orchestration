"""Independent offline checks of the fixed gold answers; no model access."""
import json
from collections import defaultdict
from pathlib import Path
r=Path(__file__).resolve().parent
d=json.loads((r/'tasks.json').read_text());g=json.loads((r/'expected.json').read_text())
# T1: sweep deltas, independently of interval-point counting.
deltas=defaultdict(int)
for a,b in d['T1']['intervals']:
 if a<b:deltas[a]+=1;deltas[b]-=1
n=0;best=-1;first=None
for t,v in sorted(deltas.items()):
 n+=v
 if n>best:best=n;first=t
assert g['T1']=={'peak':best,'earliest':first}
# T2: manual surviving transfers t3,t4,t5, and conservation.
assert g['T2']=={'A':100+9-11+7,'B':80-7,'C':60-9+11}
assert sum(g['T2'].values())==sum(d['T2']['initial'].values())
# T3: globally alphabetically sorted permutation is legal, hence lexical minimum.
x=sorted(d['T3']['nodes']);assert all(x.index(a)<x.index(b) for a,b in d['T3']['edges']);assert g['T3']==x
# T4: relational grouping without the SQL engine used by the reference generator.
rows=[]
for uid,name in d['T4']['users']:
 orders=[o for o in d['T4']['orders'] if o[1]==uid and o[3]=='paid']
 amounts=[o[2] for o in orders if o[2] is not None]
 if orders:rows.append([uid,len(orders),len(amounts),sum(amounts)])
assert g['T4']==rows
# T5: weight-indexed dynamic programming, independently of exhaustive subsets.
states={0:(0,[])}
for ident,w,v in d['T5']['items']:
 nxt=dict(states)
 for old,(val,ids) in states.items():
  nw=old+w
  if nw>d['T5']['capacity']:continue
  candidate=(val+v,ids+[ident]);prior=nxt.get(nw)
  if prior is None or (-candidate[0],candidate[1])<(-prior[0],prior[1]):nxt[nw]=candidate
 states=nxt
v,w,ids=min((-v,w,ids) for w,(v,ids) in states.items());assert g['T5']=={'ids':ids,'weight':w,'value':-v}
# T6: separately derived exact thousandths and integer round-half-even.
def cents(m):
 q,rem=divmod(m,10)
 if rem>5 or (rem==5 and q%2):q+=1
 return f'{q//100}.{q%100:02d}'
assert g['T6']==[['north',cents(10000)],['north,west',cents(1200+2005)],['south',cents(-100+5+1000)]]
print('All six fixed gold answers independently audited: PASS')

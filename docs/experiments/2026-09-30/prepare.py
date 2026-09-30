from pathlib import Path
import json,hashlib,itertools,sqlite3,csv,io
from decimal import Decimal
r=Path(__file__).resolve().parent
data={
'T1':{'intervals':[[0,3],[1,5],[3,7],[5,9],[5,5],[2,6],[6,8],[7,10],[8,11],[3,4],[4,7],[9,12]],'rule':'Half-open intervals [start,end); discard zero-length intervals. Return peak simultaneous count and earliest start time of that peak as {"peak":integer,"earliest":integer}.'},
'T2':{'initial':{'A':100,'B':80,'C':60},'events':[['x1','transfer','t1','A','B',25],['x2','transfer','t2','B','C',17],['x1','transfer','t1','A','B',25],['x3','reverse','t1'],['x4','transfer','t3','C','A',9],['x5','reverse','missing'],['x6','reverse','t1'],['x7','transfer','t4','A','C',11],['x2','transfer','t2','B','C',999],['x8','reverse','t2'],['x9','transfer','t5','B','A',7]],'rule':'Process in given order. Deduplicate by event id (first wins even if later payload differs). Transfers subtract/add specified amount, no overdraft check. Transfer ids in first occurrences are unique. Reverse undoes a known not-yet-reversed transfer once; unknown or already reversed is a no-op. Return final balances as {"A":integer,"B":integer,"C":integer}.'},
'T3':{'nodes':['A','B','C','D','E','F','G','H','I','J'],'edges':[['A','D'],['B','D'],['B','E'],['C','F'],['D','G'],['E','G'],['F','H'],['G','I'],['H','I'],['E','J']],'rule':'Edge [u,v] requires u before v. Return lexicographically smallest topological ordering as an array of node strings. At each step choose the smallest currently available node.'},
'T4':{'users':[[1,'Ada'],[2,'Bo'],[3,'Cy'],[4,'Di'],[5,'Eve']],'orders':[[11,1,10,'paid'],[12,1,None,'paid'],[13,1,8,'void'],[14,2,0,'paid'],[15,2,4,'paid'],[16,3,9,'void'],[17,None,50,'paid'],[18,5,None,'paid']],'query':"SELECT u.id,COUNT(o.id),COUNT(o.amount),COALESCE(SUM(o.amount),0) FROM users u LEFT JOIN orders o ON o.user_id=u.id AND o.status='paid' GROUP BY u.id HAVING COUNT(o.id)>0 ORDER BY u.id",'rule':'Tables users(id,name), orders(id,user_id,amount,status). null values are SQL NULL. Return query rows as arrays of integers, in query order.'},
'T5':{'capacity':25,'items':[['A',6,13],['B',4,8],['C',7,15],['D',3,6],['E',5,11],['F',9,20],['G',2,4],['H',8,17],['I',1,2],['J',10,21],['K',4,9],['L',6,12],['M',3,7],['N',5,10]],'rule':'0/1 knapsack: each [id,weight,value] can be chosen at most once; total weight <= capacity. Maximize value; ties minimize weight; remaining ties choose lexicographically smallest sorted id list using usual sequence comparison (shorter equal-prefix list first). Return {"ids":[strings],"weight":integer,"value":integer}.'},
'T6':{'csv':'group,amount,note\n"north,west",1.20,"alpha,beta"\nsouth,-0.10,"line one\nline two"\n"north,west",2.005,"a ""quote"""\nsouth,0.005,x\nnorth,10,z\nsouth,1.00,last\n','rule':'Parse CSV with comma delimiter and standard double-quote escaping, including quoted newline. Sum exact decimal amounts by exact group string; round each final sum (not each row) to 2 decimal places using round-half-even. Return sorted-by-group array of [group, formatted amount string with exactly two decimal places].'}
}
ans={}
intervals=data['T1']['intervals'];points=sorted({t for a,b in intervals if a<b for t in [a,b]});counts=[(sum(a<=t<b for a,b in intervals),t) for t in points];peak=max(c for c,t in counts);ans['T1']={'peak':peak,'earliest':min(t for c,t in counts if c==peak)}
bal=data['T2']['initial'].copy();seen=set();trans={};undone=set()
for eid,kind,tid,*args in data['T2']['events']:
 if eid in seen:continue
 seen.add(eid)
 if kind=='transfer':
  a,b,n=args;bal[a]-=n;bal[b]+=n;trans[tid]=args
 elif tid in trans and tid not in undone:
  a,b,n=trans[tid];bal[a]+=n;bal[b]-=n;undone.add(tid)
ans['T2']=bal
order=[]
while len(order)<len(data['T3']['nodes']):
 order.append(min(n for n in data['T3']['nodes'] if n not in order and all(a in order for a,b in data['T3']['edges'] if b==n)))
ans['T3']=order
con=sqlite3.connect(':memory:');con.execute('CREATE TABLE users(id,name)');con.execute('CREATE TABLE orders(id,user_id,amount,status)');con.executemany('INSERT INTO users VALUES(?,?)',data['T4']['users']);con.executemany('INSERT INTO orders VALUES(?,?,?,?)',data['T4']['orders']);ans['T4']=[list(row) for row in con.execute(data['T4']['query'])]
items=data['T5']['items'];choices=[]
for bits in itertools.product([False,True],repeat=len(items)):
 sub=[x for x,b in zip(items,bits) if b];w=sum(x[1] for x in sub);v=sum(x[2] for x in sub)
 if w<=data['T5']['capacity']:choices.append((-v,w,[x[0] for x in sub]))
nv,w,ids=min(choices);ans['T5']={'ids':ids,'weight':w,'value':-nv}
sums={}
for row in csv.DictReader(io.StringIO(data['T6']['csv'])):sums[row['group']]=sums.get(row['group'],Decimal(0))+Decimal(row['amount'])
ans['T6']=[[g,format(v.quantize(Decimal('.01')),'.2f')] for g,v in sorted(sums.items())]
prompt='Authorized bounded subscription experiment. Solve the six tasks below without tools, files, network, subagents, or external actions. Use only this prompt. Return exactly one JSON object with keys T1,T2,T3,T4,T5,T6 and each task answer as specified. No Markdown fences, explanations, or additional fields. All six tasks have equal weight.\n\n'+json.dumps(data,ensure_ascii=False,separators=(',',':'))
for filename,obj in [('tasks.json',data),('expected.json',ans)]: (r/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
(r/'prompt.txt').write_text(prompt+'\n')
manifest={name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in ['protocol.json','tasks.json','expected.json','prompt.txt']}
(r/'preregistration-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(ans,indent=2));print('Prompt bytes:',len(prompt.encode()));print(json.dumps(manifest,indent=2))

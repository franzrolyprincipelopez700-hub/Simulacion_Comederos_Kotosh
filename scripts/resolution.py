import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.schemas import Scenario
from app.engine import simulate
rows=[]
for policy in ['P0','P1','P2']:
    for step in [2,1,.5,.25]:
        c=Scenario(policy=policy,mode='determinista',step=step)
        m=simulate(c,detail=False)['metrics']; rows.append({'policy':policy,'step':step,**m})
out=Path(__file__).resolve().parents[1]/'output';out.mkdir(exist_ok=True)
(out/'resolution.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps([{k:r[k] for k in ['policy','step','shortage','consumption','work','refills']} for r in rows],indent=2))

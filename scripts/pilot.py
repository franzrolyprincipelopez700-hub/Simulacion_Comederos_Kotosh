"""Calculate a reproducible 13 x 30 pilot through the PostgreSQL worker."""
import sys,time,json,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.db import Session,Job,Run,RunDetail
from app.schemas import Scenario,ExperimentRequest
from sqlalchemy import select
from app.exports import generate

c=Scenario()
configs=[c.model_copy(update={'name':'P0 · referencia sintética'})]
for interval in [90,150]:
    for target in [.8,1]: configs.append(Scenario(**{**c.model_dump(),'name':f'P1 · {interval} min / {target*100:g}%','policy':'P1','interval':interval,'target':target}))
for threshold in [.2,.35]:
    for interval in [30,60]:
        for target in [.8,1]: configs.append(Scenario(**{**c.model_dump(),'name':f'P2 · {threshold*100:g}% / {interval} min / {target*100:g}%','policy':'P2','threshold':threshold,'interval':interval,'target':target}))
request=ExperimentRequest(name='Piloto sintético · 13 alternativas × 30 réplicas',configurations=configs)
with Session.begin() as s:
    j=Job(name=request.name,payload=request.model_dump(),total=390);s.add(j);s.flush();id=j.id
started=time.perf_counter()
while True:
    with Session() as s:
        j=s.get(Job,id)
        if j.status in ['completado','fallido','cancelado']: break
    time.sleep(.4)
elapsed=time.perf_counter()-started
if j.status!='completado': raise RuntimeError(j.error or j.status)
out=Path(__file__).resolve().parents[1]/'output';out.mkdir(exist_ok=True)
with Session() as s:
    job=s.get(Job,id);runs=s.scalars(select(Run).where(Run.job_id==id).order_by(Run.alternative,Run.replicate)).all()
    rows=[{'alternative':r.alternative,'replicate':r.replicate,'result':r.result} for r in runs];detail=s.get(RunDetail,runs[0].id)
    for fmt in ['csv','xlsx','pdf']:
        data,_=generate(job,rows,fmt,detail.series);(out/f'piloto-kotosh.{fmt}').write_bytes(data)
    report={'experiment_id':id,'replicates':390,'alternatives':13,'horizon_minutes':480,'step_minutes':1,'worker_seconds':job.elapsed,'end_to_end_seconds':elapsed,'platform':platform.platform(),'python':platform.python_version(),'summary':job.summary}
    (out/'pilot-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='summary'},ensure_ascii=False))

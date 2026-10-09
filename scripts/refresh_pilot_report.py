import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.db import Session,Job,Run,RunDetail
from app.schemas import Scenario
from app.analysis import summarize
from app.exports import generate
from sqlalchemy import select
root=Path(__file__).resolve().parents[1]
report=json.loads((root/'output/pilot-results.json').read_text(encoding='utf-8'))
with Session.begin() as s:
    job=s.get(Job,report['experiment_id']);runs=s.scalars(select(Run).where(Run.job_id==job.id).order_by(Run.alternative,Run.replicate)).all()
    rows=[{'alternative':r.alternative,'replicate':r.replicate,'result':r.result} for r in runs]
    job.summary=summarize([Scenario(**c) for c in job.payload['configurations']],rows)
    detail=s.get(RunDetail,runs[0].id)
    for fmt in ['csv','xlsx','pdf']:
        data,_=generate(job,rows,fmt,detail.series);(root/f'output/piloto-kotosh.{fmt}').write_bytes(data)
    report['summary']=job.summary
    (root/'output/pilot-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Reportes regenerados con resultados conservados del piloto.')

import csv,io
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from sqlalchemy import select,func,delete,text
from .db import Session,ScenarioRecord,ScenarioVersion,Job,Run,RunDetail,Dataset,Observation,ValidationRecord,WorkspaceSetting
from .schemas import Scenario,ExperimentRequest
from .field import preview,fingerprint,FieldRow,COLUMNS,observed_metrics
from .config import MODEL_VERSION

app=FastAPI(title='Simulador Avícola Kotosh',version=MODEL_VERSION)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5174','http://127.0.0.1:5174'],allow_methods=['*'],allow_headers=['*'])

def get(s,cls,id):
    obj=s.get(cls,id)
    if not obj: raise HTTPException(404,'Registro no encontrado')
    return obj
def job_dict(j):
    return {k:getattr(j,k) for k in ['id','name','status','progress','total','created','elapsed','error','summary','payload']}

@app.get('/api/health')
def health():
    with Session() as s: s.execute(text('SELECT 1'))
    return {'status':'ok','database':'PostgreSQL','model':MODEL_VERSION}
@app.get('/api/default')
def default(): return Scenario().model_dump()
@app.post('/api/validate')
def validate_config(c:Scenario): return c.model_dump()
@app.get('/api/overview')
def overview():
    with Session() as s:
        return {'scenarios':s.scalar(select(func.count()).select_from(ScenarioRecord)),
                'experiments':s.scalar(select(func.count()).select_from(Job)),
                'completed':s.scalar(select(func.count()).select_from(Job).where(Job.status=='completado'))}
class FieldPlan(BaseModel):
    calibration_days:int=Field(default=10,ge=1,le=365)
    validation_days:int=Field(default=5,ge=1,le=365)
@app.get('/api/field/plan')
def field_plan():
    with Session() as s:
        r=s.get(WorkspaceSetting,'field_plan')
        return r.value if r else FieldPlan().model_dump()
@app.post('/api/field/plan')
def save_field_plan(plan:FieldPlan):
    with Session.begin() as s:
        r=s.get(WorkspaceSetting,'field_plan')
        if r: r.value=plan.model_dump()
        else: s.add(WorkspaceSetting(key='field_plan',value=plan.model_dump()))
    return plan.model_dump()
@app.get('/api/scenarios')
def scenarios(q:str='',page:int=Query(1,ge=1)):
    with Session() as s:
        items=s.scalars(select(ScenarioRecord).where(ScenarioRecord.name.ilike('%'+q+'%')).order_by(ScenarioRecord.created.desc()).offset((page-1)*20).limit(20)).all()
        return [{'id':r.id,'name':r.name,'versions':[{'id':v.id,'version':v.version,'config':v.config} for v in s.scalars(select(ScenarioVersion).where(ScenarioVersion.scenario_id==r.id).order_by(ScenarioVersion.version.desc()))]} for r in items]
@app.post('/api/scenarios')
def save(c:Scenario,scenario_id:str|None=None):
    with Session.begin() as s:
        if scenario_id:
            r=get(s,ScenarioRecord,scenario_id); r.name=c.name
            v=s.scalar(select(func.max(ScenarioVersion.version)).where(ScenarioVersion.scenario_id==r.id))+1
        else:
            r=ScenarioRecord(name=c.name); s.add(r); s.flush(); v=1
        record=ScenarioVersion(scenario_id=r.id,version=v,config=c.model_dump()); s.add(record); s.flush()
        return {'id':r.id,'version':v,'version_id':record.id}
@app.post('/api/experiments',status_code=201)
def enqueue(req:ExperimentRequest):
    # Only policy/treatment parameters may differ in a paired comparison.
    treatments={'name','policy','interval','schedule','target','threshold','continuous','reference_amount','reference_delay'}
    base=req.configurations[0].model_dump()
    for c in req.configurations[1:]:
        if req.analysis_kind=='paired' and any(c.model_dump()[k]!=v for k,v in base.items() if k not in treatments): raise HTTPException(422,'Las condiciones externas deben ser iguales entre alternativas')
    with Session.begin() as s:
        j=Job(name=req.name,payload=req.model_dump(),total=sum(c.replicates for c in req.configurations)); s.add(j); s.flush()
        return job_dict(j)
@app.get('/api/experiments')
def history(q:str='',page:int=Query(1,ge=1)):
    with Session() as s: return [job_dict(j) for j in s.scalars(select(Job).where(Job.name.ilike('%'+q+'%')).order_by(Job.created.desc()).offset((page-1)*20).limit(20))]
@app.get('/api/experiments/{id}')
def experiment(id:str):
    with Session() as s: return job_dict(get(s,Job,id))
@app.post('/api/experiments/{id}/cancel')
def cancel(id:str):
    with Session.begin() as s:
        j=get(s,Job,id)
        if j.status in ['pendiente','en ejecución']:
            j.cancel=True
            if j.status=='pendiente': j.status='cancelado'
        return job_dict(j)
@app.post('/api/experiments/{id}/retry')
def retry(id:str):
    with Session.begin() as s:
        j=get(s,Job,id)
        if j.status not in ['fallido','cancelado']: raise HTTPException(409,'Solo se reintentan trabajos fallidos o cancelados')
        ids=select(Run.id).where(Run.job_id==id)
        s.execute(delete(RunDetail).where(RunDetail.run_id.in_(ids))); s.execute(delete(Run).where(Run.job_id==id))
        j.status='pendiente'; j.progress=0; j.cancel=False; j.summary=None; j.error=None; j.worker=None; j.heartbeat=None
        return job_dict(j)
@app.get('/api/experiments/{id}/runs')
def runs(id:str,page:int=Query(1,ge=1)):
    with Session() as s:
        get(s,Job,id)
        return [{'id':r.id,'alternative':r.alternative,'replicate':r.replicate,**r.result} for r in s.scalars(select(Run).where(Run.job_id==id).order_by(Run.replicate,Run.alternative).offset((page-1)*50).limit(50))]
@app.get('/api/runs/{id}/detail')
def detail(id:str,offset:int=Query(0,ge=0),limit:int=Query(1000,ge=1,le=2000)):
    with Session() as s:
        r=get(s,Run,id); d=s.get(RunDetail,id)
        return {'run':r.result,'events':d.events[offset:offset+limit] if d else [],'series':d.series[offset:offset+limit] if d else [],'total':len(d.series) if d else 0,'events_total':len(d.events) if d else 0}
@app.get('/api/experiments/{id}/export/{format}')
def export(id:str,format:str):
    from .exports import generate
    with Session() as s:
        j=get(s,Job,id)
        if j.status!='completado': raise HTTPException(409,'Solo se exportan experimentos completos')
        rows=[{'alternative':r.alternative,'replicate':r.replicate,'result':r.result} for r in s.scalars(select(Run).where(Run.job_id==id).order_by(Run.alternative,Run.replicate))]
        first=s.scalar(select(Run).where(Run.job_id==id,Run.alternative==0,Run.replicate==0)); d=s.get(RunDetail,first.id) if first else None
        if format not in ['csv','xlsx','pdf']: raise HTTPException(400,'Formato inválido')
        data,mime=generate(j,rows,format,d.series if d else [])
        return Response(data,media_type=mime,headers={'Content-Disposition':f'attachment; filename="informe-kotosh.{format}"'})

class ImportRequest(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    origin:str='observado'
    partition:str='calibración'
    text:str=Field(max_length=5000000)
    dataset_id:str|None=None
@app.get('/api/field/template')
def template():
    return Response(','.join(COLUMNS)+'\n',media_type='text/csv',headers={'Content-Disposition':'attachment; filename="plantilla-campo.csv"'})
@app.get('/api/datasets')
def datasets():
    with Session() as s:
        return [{'id':d.id,'name':d.name,'origin':d.origin,'partition':d.partition,'rows':s.scalar(select(func.count()).select_from(Observation).where(Observation.dataset_id==d.id))} for d in s.scalars(select(Dataset).order_by(Dataset.created.desc()))]
@app.post('/api/field/preview')
def field_preview(req:ImportRequest):
    with Session() as s:
        existing=s.scalars(select(Observation.fingerprint).where(Observation.dataset_id==req.dataset_id)).all() if req.dataset_id else []
        return preview(req.text,existing)
@app.post('/api/field/import')
def field_import(req:ImportRequest):
    if req.origin not in ['observado','sintético'] or req.partition not in ['calibración','validación']: raise HTTPException(422,'Origen o partición inválidos')
    with Session.begin() as s:
        d=get(s,Dataset,req.dataset_id) if req.dataset_id else Dataset(name=req.name,origin=req.origin,partition=req.partition)
        existing=s.scalars(select(Observation.fingerprint).where(Observation.dataset_id==d.id)).all() if d.id else []
        result=preview(req.text,existing)
        if result['errors'] or not result['valid']: raise HTTPException(422,result['errors'] or 'No hay filas válidas')
        s.add(d); s.flush()
        # Whole-day holdout: observed dates cannot occur in both partitions.
        if d.origin=='observado':
            other=s.scalars(select(Observation).join(Dataset).where(Dataset.origin=='observado',Dataset.partition!=d.partition)).all()
            if {o.data['date'] for o in other}&{r['date'] for r in result['valid']}: raise HTTPException(422,'Una jornada ya está en la otra partición')
        for row in result['valid']: s.add(Observation(dataset_id=d.id,fingerprint=fingerprint(row),data=row))
        return {'id':d.id,'count':len(result['valid'])}
@app.get('/api/datasets/{id}')
def dataset(id:str,page:int=Query(1,ge=1)):
    with Session() as s:
        d=get(s,Dataset,id)
        return {'name':d.name,'origin':d.origin,'partition':d.partition,'observations':[o.data for o in s.scalars(select(Observation).where(Observation.dataset_id==id).offset((page-1)*100).limit(100))]}
class ValidationRequest(BaseModel):
    experiment_id:str
    dataset_id:str
    tolerances:dict[str,float]=Field(default_factory=lambda:{'shortage':10,'waste':2,'refills':3,'work':15})
@app.post('/api/validation')
def validation(req:ValidationRequest):
    if set(req.tolerances)!={'shortage','waste','refills','work'} or any(v<0 for v in req.tolerances.values()): raise HTTPException(422,'Define tolerancias no negativas para los cuatro indicadores')
    with Session.begin() as s:
        d=get(s,Dataset,req.dataset_id); j=get(s,Job,req.experiment_id)
        if d.partition!='validación' or d.origin!='observado': raise HTTPException(422,'Se requieren jornadas observadas reservadas para validación')
        if j.status!='completado' or j.payload['configurations'][0]['policy']!='P0': raise HTTPException(422,'Se requiere experimento P0 completado')
        rows=[o.data for o in s.scalars(select(Observation).where(Observation.dataset_id==d.id))]
        days=observed_metrics(rows); out=[]
        for m,t in req.tolerances.items():
            values=[r[m] for r in days if r[m] is not None]; mean=sum(values)/len(values) if values else None
            predicted=j.summary['summaries'][0]['metrics'][m]['mean']; error=abs(predicted-mean) if mean is not None and predicted is not None else None
            out.append({'metric':m,'observed':mean,'predicted':predicted,'absolute_error':error,'tolerance':t,'accepted':error<=t if error is not None else None,'days':len(values)})
        result={'metrics':out,'message':'Comparación con jornadas reservadas. El cumplimiento numérico requiere revisar la calidad, cobertura y comparabilidad de las observaciones; no certifica por sí solo el modelo.'}
        record=ValidationRecord(dataset_id=d.id,experiment_id=j.id,criteria=req.tolerances,result=result);s.add(record);s.flush()
        return {**result,'id':record.id}
@app.get('/api/validation/history')
def validation_history():
    with Session() as s:
        return [{'id':v.id,'dataset_id':v.dataset_id,'experiment_id':v.experiment_id,'criteria':v.criteria,'result':v.result,'created':v.created} for v in s.scalars(select(ValidationRecord).order_by(ValidationRecord.created.desc()).limit(100))]

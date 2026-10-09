import time, socket, os
from datetime import timedelta
from sqlalchemy import select, delete
from .db import Session, Job, Run, RunDetail, now
from .schemas import ExperimentRequest
from .engine import simulate
from .analysis import summarize

def recover():
    with Session.begin() as s:
        stale=s.scalars(select(Job).where(Job.status=='en ejecución',Job.heartbeat<now()-timedelta(minutes=2)).with_for_update(skip_locked=True)).all()
        for j in stale: j.status='fallido'; j.error='Trabajador interrumpido. Reintentar comienza el cálculo completo.'

def process_one():
    with Session.begin() as s:
        job=s.scalar(select(Job).where(Job.status=='pendiente').order_by(Job.created).with_for_update(skip_locked=True).limit(1))
        if not job: return False
        job.status='en ejecución'; job.worker=f'{socket.gethostname()}:{os.getpid()}'; job.heartbeat=now(); job_id=job.id; payload=job.payload
    started=time.perf_counter()
    try:
        request=ExperimentRequest.model_validate(payload); configs=request.configurations; rows=[]
        for rep in range(configs[0].replicates):
            for i,c in enumerate(configs):
                with Session.begin() as s:
                    j=s.get(Job,job_id)
                    if j.cancel: j.status='cancelado'; j.elapsed=time.perf_counter()-started; return True
                    if j.status!='en ejecución': return True
                    j.heartbeat=now()
                result=simulate(c,rep,detail=rep<c.detail_replicates)
                if not result['metrics']['consistent']: raise ValueError('Balance inconsistente; resultado excluido')
                rows.append({'alternative':i,'replicate':rep,'result':{k:v for k,v in result.items() if k not in ('events','series')}})
                with Session.begin() as s:
                    j=s.get(Job,job_id)
                    r=Run(job_id=job_id,alternative=i,replicate=rep,result=rows[-1]['result']); s.add(r); s.flush()
                    if result['series']: s.add(RunDetail(run_id=r.id,events=result['events'],series=result['series']))
                    j.progress+=1; j.heartbeat=now()
        with Session.begin() as s:
            j=s.get(Job,job_id)
            j.status='cancelado' if j.cancel else 'completado'
            if not j.cancel:
                j.summary=summarize(configs,rows,request.analysis_kind)
                if request.analysis_kind=='sensitivity':
                    j.summary['recommendations']=[]
                    j.summary['message']='Sensibilidad descriptiva de entradas: no se aplican contrastes de políticas ni se declara una ganadora.'
                    j.summary['method']='Medias, desviación estándar e IC t por configuración. Bloques independientes entre réplicas.'
            j.elapsed=time.perf_counter()-started
    except Exception as exc:
        with Session.begin() as s:
            j=s.get(Job,job_id); j.status='fallido'; j.error=f'Error de cálculo: {type(exc).__name__}. Revisar configuración o integridad del modelo.'
    return True

if __name__=='__main__':
    print('Trabajador local iniciado. Ctrl+C para detener.')
    while True:
        recover()
        if not process_one(): time.sleep(1)

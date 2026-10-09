"""Finite-day SimPy model. Physical stock includes reserve; demand is a step profile."""
import simpy
import numpy as np
from .schemas import Scenario
from .policies import inspection_times, requires_reload
from .metrics import calculate

def simulate(c: Scenario, replicate=0, detail=True):
    env=simpy.Environment()
    resource=simpy.Resource(env, capacity=1)
    streams={k:np.random.default_rng(np.random.SeedSequence([c.seed,replicate,v])) for k,v in c.stream_offsets.items()}
    # Exogenous demand and duration draws are indexed by time / feeder / activity,
    # not the order in which competing policies consume RNG draws.
    ticks=int(np.ceil(c.horizon/c.step))
    demand_factors=streams['demand'].uniform(1-c.variation,1+c.variation,ticks) if c.mode=='variable' else np.ones(ticks)
    attention=streams['attention'].uniform(1-c.variation,1+c.variation,(ticks+1,len(c.feeders),6)) if c.mode=='variable' else np.ones((ticks+1,len(c.feeders),6))
    feeders=[{'id':f.id,'capacity':f.capacity,'level':f.initial,'weight':f.weight,'blocked':False,'request':'none','shortage':0.,'potential':0.,'consumed':0.,'unmet':0.,'periods':[]} for f in c.feeders]
    reserve=c.reserve; external=consumption=losses=work=0.
    refills=requests=inspections=visits=0
    events=[]; series=[]; activities=[]
    worker={'busy':False,'activity':'Disponible','feeder':None}
    def log(kind, feeder=None, **data):
        if detail: events.append({'time':float(env.now),'kind':kind,'feeder':feeder,**data})
    def snapshot():
        if detail: series.append({'time':float(env.now),'reserve':reserve,'worker':dict(worker),'feeders':[{k:f[k] for k in ('id','capacity','level','blocked','request')} for f in feeders]})
    def duration(base, idx, activity):
        return base*float(attention[min(int(env.now/c.step),ticks),idx,activity])
    def task(label, minutes, f):
        nonlocal work
        start=env.now; actual=min(minutes,c.horizon-start,c.worker_end-start)
        if actual<=0: return
        worker.update(busy=True,activity=label,feeder=f['id'])
        log('actividad_inicio',f['id'],activity=label); snapshot()
        # Accrue only the part before close; a task cut at horizon remains unfinished.
        work+=actual
        activities.append({'start':float(start),'end':float(start+actual),'activity':label,'feeder':f['id'],'completed':minutes<=actual})
        yield env.timeout(actual)
        log('actividad_fin',f['id'],activity=label)
    def serve(f,idx,repair=False,requested_at=0):
        nonlocal reserve, losses, refills, visits
        delay=c.reference_delay if c.policy=='P0' and not repair else 0
        if delay: yield env.timeout(delay)
        if env.now<c.worker_start: yield env.timeout(c.worker_start-env.now)
        with resource.request() as req:
            yield req
            if env.now>=c.worker_end: return
            f['request']='attention'; visits+=1
            log('atencion_inicio',f['id'],repair=repair); snapshot()
            for label,base,a in [('Desplazamiento',c.travel,0),('Preparación',c.preparation,1),('Resolver obstrucción' if repair else 'Carga',c.repair if repair else c.loading,3 if repair else 2)]:
                d=duration(base,idx,a)
                yield from task(label,d,f)
                if env.now>=c.worker_end or env.now>=c.horizon: return
            if repair:
                f['blocked']=False; log('obstruccion_resuelta',f['id'])
            else:
                space=max(0,min(f['capacity']-f['level'],c.target*f['capacity']-f['level']))
                if c.policy=='P0': space=min(space,c.reference_amount)
                taken=min(reserve,space/(1-c.loss_fraction)); added=taken*(1-c.loss_fraction)
                reserve-=taken; losses+=taken-added; f['level']+=added
                if added>1e-10:
                    refills+=1; log('recarga_completada',f['id'],kg=added,loss=taken-added)
                else: log('sin_reserva',f['id'])
            f['request']='none'; worker.update(busy=False,activity='Disponible',feeder=None); snapshot()
            # If an obstruction began during a refill, schedule its repair next.
            if f['blocked'] and not repair: request(f,idx,True)
    def request(f,idx,repair=False):
        nonlocal requests
        if f['request']!='none': return
        f['request']='waiting'; requests+=1
        log('solicitud',f['id'],repair=repair); snapshot()
        env.process(serve(f,idx,repair,env.now))
    def inspect():
        nonlocal inspections
        for t in inspection_times(c):
            yield env.timeout(max(0,t-env.now))
            if env.now>=c.worker_end: break
            if env.now<c.worker_start: yield env.timeout(c.worker_start-env.now)
            with resource.request() as req:
                yield req
                if env.now>=c.worker_end: break
                # One shared round, not one round per feeder.
                d=duration(c.inspection,0,4)
                yield from task('Inspección',d,feeders[0])
                if env.now>=c.worker_end or env.now>=c.horizon: break
                inspections+=1; log('inspeccion')
                for idx,f in enumerate(feeders):
                    if f['blocked']: request(f,idx,True)
                    elif requires_reload(c,f): request(f,idx)
                worker.update(busy=False,activity='Disponible',feeder=None); snapshot()
    def incident(when,idx):
        yield env.timeout(when)
        f=feeders[idx]; f['blocked']=True; log('obstruccion',f['id']); snapshot()
        # Visible incident noticed immediately. Repair still uses the same person.
        request(f,idx,True)
    def entry(e):
        nonlocal reserve,external
        yield env.timeout(e.time); reserve+=e.kg; external+=e.kg; log('entrada_externa',kg=e.kg); snapshot()
    def demand():
        nonlocal consumption
        for tick in range(ticks):
            start=env.now; end=min(c.horizon,start+c.step)
            overlap=max(0,min(end,c.service_end)-max(start,c.service_start))
            profile=c.demand_profile[min(int(start/c.horizon*len(c.demand_profile)),len(c.demand_profile)-1)]
            mass=c.demand_kg_hour*overlap/60*profile*float(demand_factors[tick])
            total_weight=sum(f['weight'] for f in feeders)
            allocations=[mass*f['weight']/total_weight for f in feeders]
            unmet=0
            for f,amount in zip(feeders,allocations):
                f['potential']+=amount
                taken=min(f['level'],amount) if not f['blocked'] else 0
                f['level']-=taken; f['consumed']+=taken; consumption+=taken; unmet+=amount-taken
            if c.redistribution and unmet>0:
                accessible=[f for f in feeders if not f['blocked'] and f['level']>0]
                stock=sum(f['level'] for f in accessible)
                extra=min(unmet,stock)
                for f in accessible:
                    taken=extra*f['level']/stock; f['level']-=taken; f['consumed']+=taken; consumption+=taken
                unmet-=extra
            # Assign system unmet proportionally; no backlog is accumulated.
            for f,a in zip(feeders,allocations):
                f['unmet']+=unmet*a/mass if mass else 0
                if overlap and (f['blocked'] or f['level']<=1e-10):
                    f['shortage']+=overlap
                    left=max(start,c.service_start); right=min(end,c.service_end)
                    if f['periods'] and abs(f['periods'][-1][1]-left)<1e-9: f['periods'][-1][1]=right
                    else: f['periods'].append([left,right])
            log('demanda',kg=mass,unmet=unmet); snapshot()
            yield env.timeout(end-start)
    # Tie order: external arrivals, obstruction, inspections, demand, queued completions.
    for e in sorted(c.entries,key=lambda e:e.time): env.process(entry(e))
    for i in c.incidents: env.process(incident(i.time,next(j for j,f in enumerate(feeders) if f['id']==i.feeder)))
    if c.mode=='variable' and c.random_incidence_probability:
        draws=streams['incidents'].random((ticks,len(feeders)))
        for idx in range(len(feeders)):
            hits=np.flatnonzero(draws[:,idx]<c.random_incidence_probability*c.step/60)
            for tick in hits: env.process(incident(float(tick*c.step),idx))
    env.process(inspect()); env.process(demand()); snapshot()
    env.run(until=c.horizon)  # [0,H); completions at H are excluded.
    snapshot()
    metrics=calculate(c,feeders,reserve,external,consumption,losses,work,refills,requests,inspections,visits)
    return {'metrics':metrics,'feeders':feeders,'events':events,'series':series,'activities':activities,
            'seed':c.seed,'replicate':replicate,'streams':c.stream_offsets,'model_version':'1.0.0'}

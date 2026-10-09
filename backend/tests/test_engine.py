import pytest
from app.schemas import Scenario,Feeder,Incident,Entry
from app.engine import simulate
from app.analysis import summarize,holm
from app.field import preview,COLUMNS,observed_metrics

def small(**kw):
    base=dict(feeders=[Feeder(id='C1',capacity=1,initial=1)],horizon=10,service_end=10,worker_end=10,
              mode='determinista',reserve=0,demand_kg_hour=3,incidents=[],schedule=[],policy='P0',inspection=0,reference_delay=0)
    base.update(kw);return Scenario(**base)
def test_manual():
    r=simulate(small());m=r['metrics']
    assert m['consumption']==pytest.approx(.5)
    assert m['final']==pytest.approx(.5)
    assert m['shortage']==0 and m['refills']==0
    assert m['potential_demand']==pytest.approx(.5)
    assert m['consistent'] and m['work']==0
@pytest.mark.parametrize('policy',['P0','P1','P2'])
def test_balance_bounds(policy):
    c=Scenario(policy=policy);r=simulate(c)
    assert r['metrics']['consistent']
    assert r['metrics']['initial']+r['metrics']['external']==pytest.approx(r['metrics']['consumption']+r['metrics']['losses']+r['metrics']['final'],abs=1e-8)
    for snap in r['series']:
        assert snap['reserve']>=-1e-8
        assert all(-1e-8<=f['level']<=f['capacity']+1e-8 for f in snap['feeders'])
def test_one_person():
    r=simulate(Scenario())
    a=sorted(r['activities'],key=lambda x:x['start'])
    assert all(a[i]['end']<=a[i+1]['start']+1e-8 for i in range(len(a)-1))
    assert sum(x['end']-x['start'] for x in a)==pytest.approx(r['metrics']['work'])
def test_inspection_detection_and_no_duplicates():
    r=simulate(small(policy='P2',interval=4,threshold=.8,reserve=4,inspection=1,loading=1,travel=0,preparation=0))
    requests=[e for e in r['events'] if e['kind']=='solicitud']
    assert requests[0]['time']==5 # threshold crossed before detection; inspect at 4 ends at 5
    state=False
    for e in r['events']:
        if e['kind']=='solicitud': assert not state;state=True
        if e['kind'] in ['recarga_completada','sin_reserva','obstruccion_resuelta']: state=False
def test_exhausted_reserve_terminates():
    r=simulate(small(feeders=[Feeder(id='C1',capacity=1,initial=0)],policy='P1',interval=1,loading=0,travel=0,preparation=0))
    assert r['metrics']['shortage']==10
    assert r['metrics']['refills']==0 and len(r['events'])<200
def test_obstruction_stock_and_union():
    r=simulate(small(demand_kg_hour=0,incidents=[Incident(time=2,feeder='C1')],travel=0,preparation=0,repair=3))
    assert any(s['feeders'][0]['blocked'] and s['feeders'][0]['level']==1 for s in r['series'])
    assert r['metrics']['shortage']==3
    empty=simulate(small(feeders=[Feeder(id='C1',capacity=1,initial=0)],incidents=[Incident(time=2,feeder='C1')],repair=3,travel=0,preparation=0))
    assert empty['metrics']['shortage']==10
def test_zero_denominator():
    r=simulate(small(feeders=[Feeder(id='C1',capacity=1,initial=0)],demand_kg_hour=0))
    assert r['metrics']['waste'] is None
def test_closing_and_partial_work():
    r=simulate(small(feeders=[Feeder(id='C1',capacity=1,initial=0)],schedule=[0],reserve=5,loading=10,travel=0,preparation=0))
    assert r['metrics']['refills']==0 and r['metrics']['pending']==1
    assert r['metrics']['work']==10 and r['metrics']['final']==5
def test_external_is_not_transfer():
    r=simulate(small(entries=[Entry(time=5,kg=2)],schedule=[6],travel=0,preparation=0,loading=0,loss_fraction=.1))
    assert r['metrics']['external']==2 and r['metrics']['consistent']
def test_reproducibility_and_independent_blocks():
    c=Scenario();assert simulate(c,3)==simulate(c,3)
    assert simulate(c,3)['metrics']!=simulate(c,4)['metrics']
def test_pairing_demand():
    a=simulate(Scenario(policy='P0'),5);b=simulate(Scenario(policy='P2'),5)
    assert [e['kg'] for e in a['events'] if e['kind']=='demanda']==[e['kg'] for e in b['events'] if e['kind']=='demanda']
def test_field_invalid_and_duplicate():
    header=','.join(COLUMNS)+'\n';line='2026-10-08,08:00,C1,suministro,1,,,nota\n'
    r=preview(header+line+line+'mal,08:00,C1,suministro,-2,,,nota\n')
    assert len(r['valid'])==1 and [e['row'] for e in r['errors']]==[3,4]
def test_field_time_union():
    rows=[dict(date='2026-10-08',time='08:00',end_time='08:10',feeder='C1',kind='interrupción'),dict(date='2026-10-08',time='08:05',end_time='08:15',feeder='C1',kind='interrupción')]
    assert observed_metrics(rows)[0]['shortage']==15
def test_holm_and_paired_analysis():
    assert holm([.01,.03,.2])==pytest.approx([.03,.06,.2])
    configs=[Scenario(policy='P0'),Scenario(policy='P2')]
    rows=[{'alternative':i,'replicate':rep,'result':simulate(c,rep,False)} for rep in range(3) for i,c in enumerate(configs)]
    s=summarize(configs,rows); assert all(c['difference']['n']==3 for c in s['comparisons'])
    assert s['recommendations']==[]
def test_invalid_config():
    with pytest.raises(ValueError): small(feeders=[Feeder(id='x',capacity=1,initial=2)])
    with pytest.raises(ValueError): small(policy='P2',threshold=1,target=1)

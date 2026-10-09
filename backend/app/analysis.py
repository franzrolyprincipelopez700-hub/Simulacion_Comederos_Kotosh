import numpy as np
from scipy import stats

METRICS=['shortage','waste','refills','work','availability']

def describe(values, alpha=.05):
    a=np.array([v for v in values if v is not None],dtype=float); n=len(a)
    if not n: return {'n':0,'mean':None,'sd':None,'low':None,'high':None}
    mean=float(a.mean()); sd=float(a.std(ddof=1)) if n>1 else None
    half=float(stats.t.ppf(1-alpha/2,n-1)*sd/np.sqrt(n)) if n>1 else None
    return {'n':n,'mean':mean,'sd':sd,'low':mean-half if half is not None else None,'high':mean+half if half is not None else None}

def holm(pvalues):
    order=sorted(range(len(pvalues)),key=lambda i:pvalues[i]); out=[1.]*len(order); previous=0
    for rank,i in enumerate(order):
        previous=max(previous,min(1.,(len(order)-rank)*pvalues[i])); out[i]=previous
    return out

def summarize(configs, rows, kind='paired'):
    alpha=configs[0].alpha; summaries=[]; comparisons=[]
    for i,c in enumerate(configs):
        selected=sorted([r for r in rows if r['alternative']==i and r['result']['metrics']['consistent']],key=lambda r:r['replicate'])
        summaries.append({'alternative':i,'name':c.name,'policy':c.policy,'metrics':{m:describe([r['result']['metrics'][m] for r in selected],alpha) for m in METRICS}})
        if i==0 or kind=='sensitivity': continue
        baseline={r['replicate']:r['result']['metrics'] for r in rows if r['alternative']==0 and r['result']['metrics']['consistent']}
        for m in METRICS[:-1]:
            diffs=[r['result']['metrics'][m]-baseline[r['replicate']][m] for r in selected if r['replicate'] in baseline and r['result']['metrics'][m] is not None and baseline[r['replicate']][m] is not None]
            d=describe(diffs,alpha); p=None
            if len(diffs)>1:
                if np.std(diffs)==0: p=None # Degenerate t contrast: report exact descriptive difference, no invented p-value.
                else: p=float(stats.ttest_1samp(diffs,0,alternative='less' if m=='shortage' else 'two-sided').pvalue)
            comparisons.append({'alternative':i,'metric':m,'difference':d,'p':p,'direction':'reducción' if m=='shortage' else 'bilateral'})
    # One predeclared family per metric across alternatives.
    for m in METRICS[:-1]:
        family=[x for x in comparisons if x['metric']==m]
        for x,p in zip(family,holm([x['p'] if x['p'] is not None else 1. for x in family])):
            x['p_holm']=p if x['p'] is not None else None
    recommendations=[]
    c=configs[0]
    if c.max_waste is None or c.max_work is None: message='Comparación descriptiva: define ambos límites operativos antes de recomendar una alternativa.'
    elif summaries[0]['metrics']['shortage']['mean']==0: message='P0 no tiene desabastecimiento: no puede demostrarse una reducción por debajo de cero.'
    else:
        eligible=[s for s in summaries[1:] if s['metrics']['waste']['high'] is not None and s['metrics']['waste']['high']<=c.max_waste and s['metrics']['work']['high']<=c.max_work]
        recommendations=sorted([s['alternative'] for s in eligible],key=lambda i:summaries[i]['metrics']['shortage']['mean'])
        message='Alternativas que cumplen límites con sus cotas superiores de confianza, ordenadas por tiempo sin alimento. Revisar evidencia y compromisos.' if eligible else 'Ninguna alternativa acredita cumplimiento de ambos límites con sus intervalos de confianza.'
    if summaries[0]['metrics']['shortage']['mean']==0 and 'debajo de cero' not in message:
        message+=' P0 no tiene desabastecimiento; no puede demostrarse una reducción por debajo de cero.'
    return {'summaries':summaries,'comparisons':comparisons,'recommendations':recommendations,'message':message,'alpha':alpha,
            'method':'IC t de Student; diferencias emparejadas por jornada; Holm por indicador. Sin calentamiento.'}

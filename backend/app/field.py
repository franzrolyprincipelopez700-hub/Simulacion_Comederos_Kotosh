import csv, io, hashlib, json
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

COLUMNS=['date','time','feeder','kind','kg','end_time','value','notes']
class FieldRow(BaseModel):
    date: str
    time: str
    feeder: str = Field(min_length=1,max_length=40)
    kind: str
    kg: float | None = Field(default=None,ge=0)
    end_time: str = ''
    value: float | None = Field(default=None,ge=0)
    notes: str = Field(default='',max_length=1000)
    @model_validator(mode='after')
    def valid(self):
        datetime.strptime(self.date,'%Y-%m-%d'); datetime.strptime(self.time,'%H:%M')
        if self.kind not in ['suministro','consumo','remanente','pérdida','inspección','recarga','actividad','interrupción','indicador']: raise ValueError('Tipo de observación desconocido')
        if self.kind in ['suministro','consumo','remanente','pérdida'] and self.kg is None: raise ValueError('Falta cantidad en kg')
        if self.kind=='indicador' and (self.value is None or self.notes not in ['shortage','waste','refills','work']): raise ValueError('Indicador: especifica value y notes como shortage, waste, refills o work')
        if self.kind in ['actividad','interrupción']:
            if not self.end_time: raise ValueError('Falta hora de fin')
            if datetime.strptime(self.end_time,'%H:%M')<=datetime.strptime(self.time,'%H:%M'): raise ValueError('El fin debe ser posterior al inicio')
        return self

def fingerprint(row): return hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def preview(text, existing=()):
    reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff'))); valid=[]; errors=[]; seen=set(existing)
    if not reader.fieldnames or set(COLUMNS)-set(reader.fieldnames): return {'valid':[],'errors':[{'row':1,'message':'Columnas requeridas: '+', '.join(COLUMNS)}]}
    for number,row in enumerate(reader,2):
        try:
            row={k:v for k,v in row.items() if k in COLUMNS}
            for k in ['kg','value']: row[k]=float(row[k]) if row.get(k) else None
            normalized=FieldRow.model_validate(row).model_dump(); fp=fingerprint(normalized)
            if fp in seen: raise ValueError('Fila duplicada')
            seen.add(fp); valid.append(normalized)
        except Exception as exc:
            message='Fila inválida: revisa fecha, horas, tipo y cantidades no negativas.'
            if isinstance(exc,ValueError) and str(exc)=='Fila duplicada': message='Fila duplicada: ya aparece en el conjunto o en este archivo.'
            if hasattr(exc,'errors'):
                details=exc.errors()
                if details and details[0].get('ctx',{}).get('error'): message=str(details[0]['ctx']['error'])
            errors.append({'row':number,'message':message})
    return {'valid':valid,'errors':errors}

def observed_metrics(rows):
    days={r['date'] for r in rows}; out=[]
    for day in sorted(days):
        selected=[r for r in rows if r['date']==day]; feeders={r['feeder'] for r in selected if r['feeder']!='SISTEMA'}
        def minutes(r):
            return (datetime.strptime(r['end_time'],'%H:%M')-datetime.strptime(r['time'],'%H:%M')).total_seconds()/60
        def union(intervals):
            merged=[]
            for a,b in sorted(intervals):
                if merged and a<=merged[-1][1]: merged[-1][1]=max(b,merged[-1][1])
                else: merged.append([a,b])
            return sum(b-a for a,b in merged)
        def intervals(group):
            return [(datetime.strptime(r['time'],'%H:%M').hour*60+datetime.strptime(r['time'],'%H:%M').minute,datetime.strptime(r['end_time'],'%H:%M').hour*60+datetime.strptime(r['end_time'],'%H:%M').minute) for r in group]
        shortage=sum(union(intervals([r for r in selected if r['kind']=='interrupción' and r['feeder']==f])) for f in feeders)/len(feeders) if feeders else None
        work=union(intervals([r for r in selected if r['kind']=='actividad'])) if any(r['kind']=='actividad' for r in selected) else None
        loss=sum(r['kg'] or 0 for r in selected if r['kind']=='pérdida'); supplied=sum(r['kg'] or 0 for r in selected if r['kind']=='suministro')
        metrics={'date':day,'shortage':shortage if any(r['kind']=='interrupción' for r in selected) else None,'work':work,'refills':sum(r['kind']=='recarga' for r in selected) if any(r['kind']=='recarga' for r in selected) else None,'waste':100*loss/supplied if supplied and any(r['kind']=='pérdida' for r in selected) else None}
        # Explicit daily system indicators allow recording a verified zero, unlike missing data.
        for r in selected:
            if r['kind']=='indicador': metrics[r['notes']]=r['value']
        out.append(metrics)
    return out

from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Feeder(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    capacity: float = Field(default=1.5, gt=0, le=100)
    initial: float = Field(default=1, ge=0)
    weight: float = Field(default=1, gt=0)
    @model_validator(mode='after')
    def valid(self):
        if self.initial > self.capacity: raise ValueError('El alimento inicial excede la capacidad')
        return self

class Entry(BaseModel):
    time: float = Field(ge=0)
    kg: float = Field(gt=0)

class Incident(BaseModel):
    time: float = Field(ge=0)
    feeder: str

class Scenario(BaseModel):
    name: str = Field(default='Jornada de demostración', min_length=1, max_length=120)
    origin: Literal['sintético','observado','fuente externa'] = 'sintético'
    provenance: dict[str, str] = Field(default_factory=lambda: {'todos':'Supuesto sintético, pendiente de verificación en campo'})
    feeders: list[Feeder] = Field(default_factory=lambda: [Feeder(id=f'C{i+1}') for i in range(3)], min_length=1, max_length=30)
    birds: int = Field(default=120, ge=1, le=100000)
    bird_description: str = 'Lote de demostración; sin modelo de crecimiento'
    horizon: float = Field(default=480, gt=0, le=1440)
    service_start: float = Field(default=0, ge=0)
    service_end: float = Field(default=480, gt=0)
    worker_start: float = Field(default=0, ge=0)
    worker_end: float = Field(default=480, gt=0)
    demand_kg_hour: float = Field(default=0.72, ge=0, le=1000)
    demand_profile: list[float] = Field(default_factory=lambda:[1], min_length=1, max_length=48)
    reserve: float = Field(default=8, ge=0, le=10000)
    entries: list[Entry] = Field(default_factory=list)
    policy: Literal['P0','P1','P2'] = 'P0'
    interval: float = Field(default=120, gt=0, le=1440)
    schedule: list[float] = Field(default_factory=lambda:[120,300])
    target: float = Field(default=1, gt=0, le=1)
    threshold: float = Field(default=0.3, ge=0, le=1)
    continuous: bool = False
    reference_amount: float = Field(default=1, gt=0)
    reference_delay: float = Field(default=10, ge=0, le=600)
    inspection: float = Field(default=2, ge=0, le=600)
    travel: float = Field(default=2, ge=0, le=600)
    preparation: float = Field(default=2, ge=0, le=600)
    loading: float = Field(default=3, ge=0, le=600)
    repair: float = Field(default=12, gt=0, le=600)
    loss_fraction: float = Field(default=0.02, ge=0, lt=1)
    redistribution: bool = True
    incidents: list[Incident] = Field(default_factory=lambda:[Incident(time=210, feeder='C2')])
    random_incidence_probability: float = Field(default=0, ge=0, le=1)
    mode: Literal['determinista','variable'] = 'variable'
    variation: float = Field(default=0.2, ge=0, le=0.95)
    step: float = Field(default=1, ge=0.1, le=10)
    seed: int = Field(default=2026, ge=0, le=2**31-1)
    stream_offsets: dict[str,int] = Field(default_factory=lambda:{'demand':11,'attention':22,'incidents':33})
    replicates: int = Field(default=30, ge=1, le=500)
    detail_replicates: int = Field(default=1, ge=0, le=10)
    max_waste: float | None = Field(default=None, ge=0, le=100)
    max_work: float | None = Field(default=None, ge=0)
    limits_origin: str = 'Sin límites operativos definidos'
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    @model_validator(mode='after')
    def valid(self):
        ids=[f.id for f in self.feeders]
        if len(set(ids)) != len(ids): raise ValueError('Identificaciones de comederos repetidas')
        if not 0 <= self.service_start < self.service_end <= self.horizon: raise ValueError('Ventana de servicio fuera de la jornada')
        if not 0 <= self.worker_start < self.worker_end <= self.horizon: raise ValueError('Disponibilidad del responsable fuera de la jornada')
        if any(i.feeder not in ids or i.time >= self.horizon for i in self.incidents): raise ValueError('Incidencia fuera de la jornada o comedero inexistente')
        if any(t<0 or t>=self.horizon for t in self.schedule): raise ValueError('Horario fuera de la jornada')
        if any(e.time>=self.horizon for e in self.entries): raise ValueError('Entrada externa fuera de la jornada')
        if any(x<0 for x in self.demand_profile): raise ValueError('Perfil de demanda negativo')
        if set(self.stream_offsets)!={'demand','attention','incidents'} or len(set(self.stream_offsets.values()))!=3: raise ValueError('Se requieren tres flujos aleatorios distintos')
        if any(v<0 or v>2**32-1 for v in self.stream_offsets.values()): raise ValueError('Identificadores de flujos fuera del rango permitido')
        if self.policy=='P2' and self.threshold>=self.target: raise ValueError('El umbral debe ser menor que el objetivo')
        return self

class ExperimentRequest(BaseModel):
    name: str = Field(min_length=1,max_length=120)
    configurations: list[Scenario] = Field(min_length=1,max_length=30)
    exploratory: bool = True
    analysis_kind: Literal['paired','sensitivity'] = 'paired'
    @model_validator(mode='after')
    def valid(self):
        base=self.configurations[0]
        if len(self.configurations)>1 and base.policy!='P0': raise ValueError('La primera alternativa debe ser P0')
        for c in self.configurations:
            if c.replicates!=base.replicates or c.seed!=base.seed: raise ValueError('Réplicas y semillas deben ser iguales dentro del bloque')
        if sum(c.replicates*c.horizon/c.step*len(c.feeders) for c in self.configurations)>20_000_000: raise ValueError('Experimento demasiado grande: reduce réplicas, horizonte o número de comederos')
        return self

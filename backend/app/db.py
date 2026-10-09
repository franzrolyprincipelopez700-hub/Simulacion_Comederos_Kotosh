import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, DateTime, Integer, ForeignKey, UniqueConstraint, CheckConstraint, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import DATABASE_URL

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class ScenarioRecord(Base):
    __tablename__='scenarios'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(120),index=True)
    created: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class ScenarioVersion(Base):
    __tablename__='scenario_versions'
    __table_args__=(UniqueConstraint('scenario_id','version'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    scenario_id: Mapped[str]=mapped_column(ForeignKey('scenarios.id'),index=True)
    version: Mapped[int]=mapped_column(Integer)
    config: Mapped[dict]=mapped_column(JSONB)
    created: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Job(Base):
    __tablename__='experiments'
    __table_args__=(CheckConstraint("status in ('pendiente','en ejecución','completado','cancelado','fallido')"),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(120),index=True)
    status: Mapped[str]=mapped_column(String(30),default='pendiente',index=True)
    payload: Mapped[dict]=mapped_column(JSONB)
    progress: Mapped[int]=mapped_column(Integer,default=0)
    total: Mapped[int]=mapped_column(Integer)
    summary: Mapped[dict | None]=mapped_column(JSONB,nullable=True)
    cancel: Mapped[bool]=mapped_column(default=False)
    worker: Mapped[str | None]=mapped_column(String(100),nullable=True)
    heartbeat: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True)
    error: Mapped[str | None]=mapped_column(Text,nullable=True)
    created: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
    elapsed: Mapped[float | None]=mapped_column(Float,nullable=True)
class Run(Base):
    __tablename__='runs'
    __table_args__=(UniqueConstraint('job_id','alternative','replicate'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    job_id: Mapped[str]=mapped_column(ForeignKey('experiments.id'),index=True)
    alternative: Mapped[int]=mapped_column(Integer)
    replicate: Mapped[int]=mapped_column(Integer)
    result: Mapped[dict]=mapped_column(JSONB)
class RunDetail(Base):
    __tablename__='run_details'
    run_id: Mapped[str]=mapped_column(ForeignKey('runs.id'),primary_key=True)
    events: Mapped[list]=mapped_column(JSONB)
    series: Mapped[list]=mapped_column(JSONB)
class Dataset(Base):
    __tablename__='datasets'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    name: Mapped[str]=mapped_column(String(120))
    origin: Mapped[str]=mapped_column(String(30))
    partition: Mapped[str]=mapped_column(String(30))
    created: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Observation(Base):
    __tablename__='observations'
    __table_args__=(UniqueConstraint('dataset_id','fingerprint'),)
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    dataset_id: Mapped[str]=mapped_column(ForeignKey('datasets.id'),index=True)
    fingerprint: Mapped[str]=mapped_column(String(64))
    data: Mapped[dict]=mapped_column(JSONB)

class ValidationRecord(Base):
    __tablename__='validation_records'
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    dataset_id: Mapped[str]=mapped_column(ForeignKey('datasets.id'),index=True)
    experiment_id: Mapped[str]=mapped_column(ForeignKey('experiments.id'),index=True)
    criteria: Mapped[dict]=mapped_column(JSONB)
    result: Mapped[dict | None]=mapped_column(JSONB,nullable=True)
    created: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class WorkspaceSetting(Base):
    __tablename__='workspace_settings'
    key: Mapped[str]=mapped_column(String(80),primary_key=True)
    value: Mapped[dict]=mapped_column(JSONB)

engine=create_engine(DATABASE_URL,pool_pre_ping=True) if DATABASE_URL else None
Session=sessionmaker(engine,expire_on_commit=False)

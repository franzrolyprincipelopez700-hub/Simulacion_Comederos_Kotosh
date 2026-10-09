import pytest
from sqlalchemy import select,delete
from app.db import Session,Job,Run,RunDetail,ScenarioRecord,ScenarioVersion,Dataset,Observation,ValidationRecord

@pytest.fixture(scope='session',autouse=True)
def clean_owned_test_records():
    yield
    with Session.begin() as s:
        jobs=select(Job.id).where(Job.name.like('TEST-%'))
        runs=select(Run.id).where(Run.job_id.in_(jobs))
        datasets=select(Dataset.id).where(Dataset.name.like('TEST-%'))
        scenarios=select(ScenarioRecord.id).where(ScenarioRecord.name.like('TEST-%'))
        s.execute(delete(ValidationRecord).where(ValidationRecord.experiment_id.in_(jobs)))
        s.execute(delete(RunDetail).where(RunDetail.run_id.in_(runs)));s.execute(delete(Run).where(Run.job_id.in_(jobs)));s.execute(delete(Job).where(Job.id.in_(jobs)))
        s.execute(delete(Observation).where(Observation.dataset_id.in_(datasets)));s.execute(delete(Dataset).where(Dataset.id.in_(datasets)))
        s.execute(delete(ScenarioVersion).where(ScenarioVersion.scenario_id.in_(scenarios)));s.execute(delete(ScenarioRecord).where(ScenarioRecord.id.in_(scenarios)))

from sqlalchemy import select
from .db import Session,ScenarioRecord,ScenarioVersion
from .schemas import Scenario
def seed():
    with Session.begin() as s:
        name='Demostración sintética · tres comederos'
        if not s.scalar(select(ScenarioRecord).where(ScenarioRecord.name==name)):
            r=ScenarioRecord(name=name); s.add(r); s.flush()
            s.add(ScenarioVersion(scenario_id=r.id,version=1,config=Scenario(name=name).model_dump()))
    print('Demostración disponible; datos existentes conservados.')
if __name__=='__main__': seed()

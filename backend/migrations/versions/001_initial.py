"""Initial PostgreSQL schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision='001'
down_revision=None
branch_labels=None
depends_on=None
def idcol(): return sa.Column('id',sa.String(36),primary_key=True)
def created(): return sa.Column('created',sa.DateTime(timezone=True),nullable=False)
def upgrade():
    op.create_table('scenarios',idcol(),sa.Column('name',sa.String(120),nullable=False),created())
    op.create_index('ix_scenarios_name','scenarios',['name'])
    op.create_table('scenario_versions',idcol(),sa.Column('scenario_id',sa.String(36),sa.ForeignKey('scenarios.id'),nullable=False),sa.Column('version',sa.Integer,nullable=False),sa.Column('config',JSONB,nullable=False),created(),sa.UniqueConstraint('scenario_id','version'))
    op.create_index('ix_scenario_versions_scenario_id','scenario_versions',['scenario_id'])
    op.create_table('experiments',idcol(),sa.Column('name',sa.String(120),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('payload',JSONB,nullable=False),sa.Column('progress',sa.Integer,nullable=False),sa.Column('total',sa.Integer,nullable=False),sa.Column('summary',JSONB),sa.Column('cancel',sa.Boolean,nullable=False),sa.Column('worker',sa.String(100)),sa.Column('heartbeat',sa.DateTime(timezone=True)),sa.Column('error',sa.Text),created(),sa.Column('elapsed',sa.Float),sa.CheckConstraint("status in ('pendiente','en ejecución','completado','cancelado','fallido')"))
    for column in ['name','status','created']: op.create_index('ix_experiments_'+column,'experiments',[column])
    op.create_table('runs',idcol(),sa.Column('job_id',sa.String(36),sa.ForeignKey('experiments.id'),nullable=False),sa.Column('alternative',sa.Integer,nullable=False),sa.Column('replicate',sa.Integer,nullable=False),sa.Column('result',JSONB,nullable=False),sa.UniqueConstraint('job_id','alternative','replicate'))
    op.create_index('ix_runs_job_id','runs',['job_id'])
    op.create_table('run_details',sa.Column('run_id',sa.String(36),sa.ForeignKey('runs.id'),primary_key=True),sa.Column('events',JSONB,nullable=False),sa.Column('series',JSONB,nullable=False))
    op.create_table('datasets',idcol(),sa.Column('name',sa.String(120),nullable=False),sa.Column('origin',sa.String(30),nullable=False),sa.Column('partition',sa.String(30),nullable=False),created())
    op.create_table('observations',idcol(),sa.Column('dataset_id',sa.String(36),sa.ForeignKey('datasets.id'),nullable=False),sa.Column('fingerprint',sa.String(64),nullable=False),sa.Column('data',JSONB,nullable=False),sa.UniqueConstraint('dataset_id','fingerprint'))
    op.create_index('ix_observations_dataset_id','observations',['dataset_id'])
def downgrade():
    for table in ['observations','datasets','run_details','runs','experiments','scenario_versions','scenarios']: op.drop_table(table)

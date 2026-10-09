"""Persist validation criteria and comparisons."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision='002'
down_revision='001'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('validation_records',sa.Column('id',sa.String(36),primary_key=True),sa.Column('dataset_id',sa.String(36),sa.ForeignKey('datasets.id'),nullable=False),sa.Column('experiment_id',sa.String(36),sa.ForeignKey('experiments.id'),nullable=False),sa.Column('criteria',JSONB,nullable=False),sa.Column('result',JSONB),sa.Column('created',sa.DateTime(timezone=True),nullable=False))
    for column in ['dataset_id','experiment_id']: op.create_index('ix_validation_records_'+column,'validation_records',[column])
def downgrade(): op.drop_table('validation_records')

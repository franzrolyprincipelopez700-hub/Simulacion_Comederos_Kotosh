"""Editable fieldwork planning."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision='003'
down_revision='002'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('workspace_settings',sa.Column('key',sa.String(80),primary_key=True),sa.Column('value',JSONB,nullable=False))
def downgrade(): op.drop_table('workspace_settings')

"""add user_id and tenant_id to runs"""
from alembic import op
import sqlalchemy as sa

revision = 'add_user_id_to_runs'
down_revision = 'drop_tables_2026'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('runs', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('runs', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True))
    op.create_index('ix_runs_user_id', 'runs', ['user_id'])
    op.create_index('ix_runs_tenant_id', 'runs', ['tenant_id'])
    # Backfill existing rows to current user (admin / seed) so NULLs are eliminated
    # Then make non-nullable in a follow-up migration


def downgrade():
    op.drop_index('ix_runs_tenant_id', table_name='runs')
    op.drop_index('ix_runs_user_id', table_name='runs')
    op.drop_column('runs', 'tenant_id')
    op.drop_column('runs', 'user_id')

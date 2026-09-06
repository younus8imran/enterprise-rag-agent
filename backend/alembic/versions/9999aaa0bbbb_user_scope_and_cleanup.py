"""user-scoped runs/documents + drop enterprise tables"""
from alembic import op
import sqlalchemy as sa

revision = 'user_scope_and_cleanup_9999'
down_revision = 'aabbccdd0011'
branch_labels = None
depends_on = None


def upgrade():
    # runs: add user_id + tenant_id (idempotent)
    for col_name, col_def in [
        ('user_id', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)),
        ('tenant_id', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id'), nullable=True)),
    ]:
        col_exists = op.get_bind().dialect.has_table(op.get_bind(), 'runs') and _column_exists('runs', col_name)
        if not col_exists:
            op.add_column('runs', col_def)
            try:
                op.create_index(f'ix_runs_{col_name}', 'runs', [col_name])
            except Exception:
                pass

    # documents: add user_id (idempotent)
    if not _column_exists('documents', 'user_id'):
        op.add_column('documents', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, server_default='1'))
        try:
            op.create_index('ix_documents_user_id', 'documents', ['user_id'])
        except Exception:
            pass

    # drop enterprise tables (idempotent)
    for table in ['regions', 'departments', 'employees', 'products', 'customers', 'orders', 'order_items', 'expenses']:
        try:
            op.drop_table(table)
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index('ix_documents_user_id', table_name='documents')
    except Exception:
        pass
    op.drop_column('documents', 'user_id')
    try:
        op.drop_index('ix_runs_tenant_id', table_name='runs')
    except Exception:
        pass
    try:
        op.drop_index('ix_runs_user_id', table_name='runs')
    except Exception:
        pass
    op.drop_column('runs', 'tenant_id')
    op.drop_column('runs', 'user_id')


def _column_exists(table: str, column: str) -> bool:
    try:
        from sqlalchemy import inspect
        insp = inspect(op.get_bind())
        return column in [c['name'] for c in insp.get_columns(table)]
    except Exception:
        return False

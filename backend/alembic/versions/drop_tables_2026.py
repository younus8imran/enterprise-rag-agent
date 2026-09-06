"""drop removed enterprise tables"""
from alembic import op
import sqlalchemy as sa

revision = 'drop_tables_2026'
down_revision = 'add_user_id_to_runs'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('regions')
    op.drop_table('departments')
    op.drop_table('employees')
    op.drop_table('products')
    op.drop_table('customers')
    op.drop_table('orders')
    op.drop_table('order_items')
    op.drop_table('expenses')


def downgrade():
    pass

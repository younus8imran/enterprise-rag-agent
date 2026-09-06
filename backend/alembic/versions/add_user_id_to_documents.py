"""add user_id to documents"""
from alembic import op
import sqlalchemy as sa

revision = 'add_user_id_to_documents'
down_revision = 'add_user_id_to_runs'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('documents', sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, server_default='1'))
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])


def downgrade():
    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_column('documents', 'user_id')

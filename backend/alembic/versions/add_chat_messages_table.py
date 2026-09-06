"""add_chat_messages_table

Revision ID: aabbccdd0011
Revises: 9999aaa0bbbb
Create Date: 2026-09-06 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'aabbccdd0011'
down_revision: Union[str, Sequence[str], None] = '9999aaa0bbbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])

def downgrade() -> None:
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_table('chat_messages')

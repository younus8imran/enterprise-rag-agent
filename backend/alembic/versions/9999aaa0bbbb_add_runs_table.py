"""add_runs_table

Revision ID: 9999aaa0bbbb
Revises: c0a1b2c3d4e5
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9999aaa0bbbb'
down_revision: Union[str, Sequence[str], None] = 'c0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('progress', sa.Float(), nullable=True, server_default=sa.text('0.0')),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

def downgrade() -> None:
    op.drop_table('runs')

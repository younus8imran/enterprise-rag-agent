"""add username to users

Revision ID: c0a1b2c3d4e5
Revises: 8492ae58e43b
Create Date: 2026-09-05 13:51:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "8492ae58e43b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(), nullable=True))
    op.execute("UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL")
    op.alter_column("users", "username", nullable=False, existing_type=sa.String())
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")

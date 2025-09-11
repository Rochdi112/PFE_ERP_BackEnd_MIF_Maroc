"""add is_active column to users

Revision ID: e576b04091b6
Revises: 5bd306f33b2b
Create Date: 2025-07-20 16:35:15.652556

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e576b04091b6"
down_revision: Union[str, Sequence[str], None] = "5bd306f33b2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_active column to users table
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "is_active")

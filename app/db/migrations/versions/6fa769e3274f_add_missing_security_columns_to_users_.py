"""Add missing security columns to users table

Revision ID: 6fa769e3274f
Revises: a30f987678fe
Create Date: 2025-09-08 00:38:39.861439

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6fa769e3274f'
down_revision: Union[str, Sequence[str], None] = 'a30f987678fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing security columns to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(), nullable=False, default=sa.func.now()))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove security columns from users table
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')

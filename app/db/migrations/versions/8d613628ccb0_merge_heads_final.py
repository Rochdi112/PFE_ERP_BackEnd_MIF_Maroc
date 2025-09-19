"""merge_heads_final

Revision ID: 8d613628ccb0
Revises: 0bde5032da9a, f1234567890a
Create Date: 2025-09-11 01:55:35.051159

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8d613628ccb0'
down_revision: Union[str, Sequence[str], None] = ('0bde5032da9a', 'f1234567890a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""merge_heads_for_techniciens_update

Revision ID: 0bde5032da9a
Revises: 34a6466da3d4, 6fa769e3274f
Create Date: 2025-09-08 00:41:25.450001

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0bde5032da9a'
down_revision: Union[str, Sequence[str], None] = ('34a6466da3d4', '6fa769e3274f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

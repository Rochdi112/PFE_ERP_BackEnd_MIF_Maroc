"""sync schema with current models

Revision ID: 77c31bf560ed
Revises: df44b376bc8a
Create Date: 2025-09-07 18:42:16.868065

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "77c31bf560ed"
down_revision: Union[str, Sequence[str], None] = "df44b376bc8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """"Upgrade schema."""
    # This migration was problematic and has been replaced by a30f987678fe
    # Keeping this file to maintain migration chain integrity
    pass


def downgrade() -> None:
    """"Downgrade schema."""
    pass

"""merge multiple heads

Revision ID: 34a6466da3d4
Revises: 8cafe646bd2e, 863cce1401db, 77c31bf560ed
Create Date: 2025-01-11 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34a6466da3d4"
down_revision: Union[str, Sequence[str], None] = ("8cafe646bd2e", "863cce1401db", "77c31bf560ed")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a merge revision - no schema changes needed
    # All schema changes are already handled by the merged revisions
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a merge revision - no schema changes to reverse
    # Individual migrations will handle their own downgrades
    pass

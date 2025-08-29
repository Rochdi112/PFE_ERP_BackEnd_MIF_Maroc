"""Initial full migration from models

Revision ID: bb94288d88f3
Revises: e576b04091b6
Create Date: 2025-07-20 17:03:13.121042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb94288d88f3'
down_revision: Union[str, Sequence[str], None] = 'e576b04091b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch operations for SQLite compatibility
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None
    if dialect == 'sqlite':
        # Only apply NOT NULL alterations; skip FK rewrites on SQLite
        with op.batch_alter_table('historiques_interventions', schema=None) as batch_op:
            batch_op.alter_column('intervention_id', existing_type=sa.INTEGER(), nullable=False)
            batch_op.alter_column('user_id', existing_type=sa.INTEGER(), nullable=False)
        with op.batch_alter_table('techniciens', schema=None) as batch_op:
            batch_op.alter_column('user_id', existing_type=sa.INTEGER(), nullable=False)
    else:
        # documents: FK to interventions with CASCADE
        op.drop_constraint(op.f('documents_intervention_id_fkey'), 'documents', type_='foreignkey')
        op.create_foreign_key(None, 'documents', 'interventions', ['intervention_id'], ['id'], ondelete='CASCADE')

        # historiques_interventions: set NOT NULL and cascade FKs
        op.alter_column('historiques_interventions', 'intervention_id', existing_type=sa.INTEGER(), nullable=False)
        op.alter_column('historiques_interventions', 'user_id', existing_type=sa.INTEGER(), nullable=False)
        op.drop_constraint(op.f('historiques_interventions_intervention_id_fkey'), 'historiques_interventions', type_='foreignkey')
        op.drop_constraint(op.f('historiques_interventions_user_id_fkey'), 'historiques_interventions', type_='foreignkey')
        op.create_foreign_key(None, 'historiques_interventions', 'interventions', ['intervention_id'], ['id'], ondelete='CASCADE')
        op.create_foreign_key(None, 'historiques_interventions', 'users', ['user_id'], ['id'], ondelete='CASCADE')

        # interventions: adjust FKs
        op.drop_constraint(op.f('interventions_equipement_id_fkey'), 'interventions', type_='foreignkey')
        op.drop_constraint(op.f('interventions_technicien_id_fkey'), 'interventions', type_='foreignkey')
        op.create_foreign_key(None, 'interventions', 'techniciens', ['technicien_id'], ['id'], ondelete='SET NULL')
        op.create_foreign_key(None, 'interventions', 'equipements', ['equipement_id'], ['id'], ondelete='CASCADE')

        # notifications: cascade FKs
        op.drop_constraint(op.f('notifications_intervention_id_fkey'), 'notifications', type_='foreignkey')
        op.drop_constraint(op.f('notifications_user_id_fkey'), 'notifications', type_='foreignkey')
        op.create_foreign_key(None, 'notifications', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        op.create_foreign_key(None, 'notifications', 'interventions', ['intervention_id'], ['id'], ondelete='CASCADE')

        # plannings: cascade FK to equipements
        op.drop_constraint(op.f('plannings_equipement_id_fkey'), 'plannings', type_='foreignkey')
        op.create_foreign_key(None, 'plannings', 'equipements', ['equipement_id'], ['id'], ondelete='CASCADE')

        # technicien_competence: cascade FKs
        op.drop_constraint(op.f('technicien_competence_competence_id_fkey'), 'technicien_competence', type_='foreignkey')
        op.drop_constraint(op.f('technicien_competence_technicien_id_fkey'), 'technicien_competence', type_='foreignkey')
        op.create_foreign_key(None, 'technicien_competence', 'competences', ['competence_id'], ['id'], ondelete='CASCADE')
        op.create_foreign_key(None, 'technicien_competence', 'techniciens', ['technicien_id'], ['id'], ondelete='CASCADE')

        # techniciens: set NOT NULL and cascade FK to users
        op.alter_column('techniciens', 'user_id', existing_type=sa.INTEGER(), nullable=False)
        op.drop_constraint(op.f('techniciens_user_id_fkey'), 'techniciens', type_='foreignkey')
        op.create_foreign_key(None, 'techniciens', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    if dialect == 'sqlite':
        # Only reverse NOT NULL changes; leave FKs as-is
        with op.batch_alter_table('historiques_interventions', schema=None) as batch_op:
            batch_op.alter_column('user_id', existing_type=sa.INTEGER(), nullable=True)
            batch_op.alter_column('intervention_id', existing_type=sa.INTEGER(), nullable=True)
        with op.batch_alter_table('techniciens', schema=None) as batch_op:
            batch_op.alter_column('user_id', existing_type=sa.INTEGER(), nullable=True)
    else:
        op.drop_constraint(None, 'techniciens', type_='foreignkey')
        op.create_foreign_key(op.f('techniciens_user_id_fkey'), 'techniciens', 'users', ['user_id'], ['id'])
        op.alter_column('techniciens', 'user_id', existing_type=sa.INTEGER(), nullable=True)

        op.drop_constraint(None, 'technicien_competence', type_='foreignkey')
        op.drop_constraint(None, 'technicien_competence', type_='foreignkey')
        op.create_foreign_key(op.f('technicien_competence_technicien_id_fkey'), 'technicien_competence', 'techniciens', ['technicien_id'], ['id'])
        op.create_foreign_key(op.f('technicien_competence_competence_id_fkey'), 'technicien_competence', 'competences', ['competence_id'], ['id'])

        op.drop_constraint(None, 'plannings', type_='foreignkey')
        op.create_foreign_key(op.f('plannings_equipement_id_fkey'), 'plannings', 'equipements', ['equipement_id'], ['id'])

        op.drop_constraint(None, 'notifications', type_='foreignkey')
        op.drop_constraint(None, 'notifications', type_='foreignkey')
        op.create_foreign_key(op.f('notifications_user_id_fkey'), 'notifications', 'users', ['user_id'], ['id'])
        op.create_foreign_key(op.f('notifications_intervention_id_fkey'), 'notifications', 'interventions', ['intervention_id'], ['id'])

        op.drop_constraint(None, 'interventions', type_='foreignkey')
        op.drop_constraint(None, 'interventions', type_='foreignkey')
        op.create_foreign_key(op.f('interventions_technicien_id_fkey'), 'interventions', 'techniciens', ['technicien_id'], ['id'])
        op.create_foreign_key(op.f('interventions_equipement_id_fkey'), 'interventions', 'equipements', ['equipement_id'], ['id'])

        op.drop_constraint(None, 'historiques_interventions', type_='foreignkey')
        op.drop_constraint(None, 'historiques_interventions', type_='foreignkey')
        op.create_foreign_key(op.f('historiques_interventions_user_id_fkey'), 'historiques_interventions', 'users', ['user_id'], ['id'])
        op.create_foreign_key(op.f('historiques_interventions_intervention_id_fkey'), 'historiques_interventions', 'interventions', ['intervention_id'], ['id'])
        op.alter_column('historiques_interventions', 'user_id', existing_type=sa.INTEGER(), nullable=True)
        op.alter_column('historiques_interventions', 'intervention_id', existing_type=sa.INTEGER(), nullable=True)

        op.drop_constraint(None, 'documents', type_='foreignkey')
        op.create_foreign_key(op.f('documents_intervention_id_fkey'), 'documents', 'interventions', ['intervention_id'], ['id'])

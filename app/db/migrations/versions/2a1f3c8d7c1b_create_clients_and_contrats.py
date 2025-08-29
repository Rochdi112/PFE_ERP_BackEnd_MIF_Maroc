"""Create clients and contrats base tables

Revision ID: 2a1f3c8d7c1b
Revises: bb94288d88f3
Create Date: 2025-08-19 00:00:00

This migration creates the core tables required by later migrations that
add foreign keys from interventions to clients/contrats.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2a1f3c8d7c1b'
down_revision: Union[str, Sequence[str], None] = 'bb94288d88f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else None

    # Create clients table (minimal viable schema)
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('nom_entreprise', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('NOW()') if dialect != 'sqlite' else None),
        sa.Column('date_modification', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)
    op.create_index('ix_clients_email', 'clients', ['email'], unique=True)

    # Create contrats table (minimal viable schema)
    op.create_table(
        'contrats',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('numero_contrat', sa.String(length=50), nullable=False),
        sa.Column('nom_contrat', sa.String(length=255), nullable=False),
        sa.Column('date_debut', sa.Date(), nullable=False),
        sa.Column('date_fin', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('NOW()') if dialect != 'sqlite' else None),
        sa.Column('date_modification', sa.DateTime(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('numero_contrat'),
    )
    op.create_index(op.f('ix_contrats_id'), 'contrats', ['id'], unique=False)
    op.create_index('ix_contrats_client', 'contrats', ['client_id'], unique=False)



def downgrade() -> None:
    op.drop_index('ix_contrats_client', table_name='contrats')
    op.drop_index(op.f('ix_contrats_id'), table_name='contrats')
    op.drop_table('contrats')

    op.drop_index('ix_clients_email', table_name='clients')
    op.drop_index(op.f('ix_clients_id'), table_name='clients')
    op.drop_table('clients')

"""Add missing equipement columns

Revision ID: a30f987678fe
Revises: 34a6466da3d4
Create Date: 2025-09-08 00:27:19.062482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a30f987678fe'
down_revision: Union[str, Sequence[str], None] = 'df44b376bc8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns to equipements table
    op.add_column('equipements', sa.Column('numero_serie', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('code_interne', sa.String(50), nullable=True))
    op.add_column('equipements', sa.Column('type_equipement', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('marque', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('modele', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('batiment', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('etage', sa.String(20), nullable=True))
    op.add_column('equipements', sa.Column('zone', sa.String(100), nullable=True))
    op.add_column('equipements', sa.Column('statut', sa.String(20), nullable=False, server_default='operationnel'))
    op.add_column('equipements', sa.Column('criticite', sa.String(20), nullable=False, server_default='standard'))
    op.add_column('equipements', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('equipements', sa.Column('specifications_techniques', sa.Text(), nullable=True))
    op.add_column('equipements', sa.Column('puissance', sa.Numeric(10, 2), nullable=True))
    op.add_column('equipements', sa.Column('poids', sa.Numeric(10, 2), nullable=True))
    op.add_column('equipements', sa.Column('frequence_entretien_jours', sa.Integer(), nullable=True))
    op.add_column('equipements', sa.Column('duree_garantie_mois', sa.Integer(), nullable=True))
    op.add_column('equipements', sa.Column('cout_acquisition', sa.Integer(), nullable=True))
    op.add_column('equipements', sa.Column('date_acquisition', sa.DateTime(), nullable=True))
    op.add_column('equipements', sa.Column('date_mise_en_service', sa.DateTime(), nullable=True))
    op.add_column('equipements', sa.Column('date_fin_garantie', sa.DateTime(), nullable=True))
    op.add_column('equipements', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('equipements', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('equipements', sa.Column('client_id', sa.Integer(), nullable=True))
    op.add_column('equipements', sa.Column('contrat_id', sa.Integer(), nullable=True))
    
    # Create indexes for better performance
    op.create_index('ix_equipements_numero_serie', 'equipements', ['numero_serie'], unique=True)
    op.create_index('ix_equipements_code_interne', 'equipements', ['code_interne'], unique=True)
    op.create_index('ix_equipements_type_equipement', 'equipements', ['type_equipement'])
    op.create_index('ix_equipements_statut', 'equipements', ['statut'])
    op.create_index('ix_equipements_criticite', 'equipements', ['criticite'])
    op.create_index('ix_equipements_client_id', 'equipements', ['client_id'])
    op.create_index('ix_equipements_contrat_id', 'equipements', ['contrat_id'])
    op.create_index('ix_equipements_created_at', 'equipements', ['created_at'])
    
    # Create composite indexes
    op.create_index('idx_equipement_type_localisation', 'equipements', ['type_equipement', 'localisation'])
    op.create_index('idx_equipement_statut_criticite', 'equipements', ['statut', 'criticite'])
    op.create_index('idx_equipement_client_statut', 'equipements', ['client_id', 'statut'])
    op.create_index('idx_equipement_created_type', 'equipements', ['created_at', 'type_equipement'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_equipements_client_id', 'equipements', 'clients', ['client_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_equipements_contrat_id', 'equipements', 'contrats', ['contrat_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraints
    op.drop_constraint('fk_equipements_contrat_id', 'equipements', type_='foreignkey')
    op.drop_constraint('fk_equipements_client_id', 'equipements', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_equipement_created_type', table_name='equipements')
    op.drop_index('idx_equipement_client_statut', table_name='equipements')
    op.drop_index('idx_equipement_statut_criticite', table_name='equipements')
    op.drop_index('idx_equipement_type_localisation', table_name='equipements')
    op.drop_index('ix_equipements_created_at', table_name='equipements')
    op.drop_index('ix_equipements_contrat_id', table_name='equipements')
    op.drop_index('ix_equipements_client_id', table_name='equipements')
    op.drop_index('ix_equipements_criticite', table_name='equipements')
    op.drop_index('ix_equipements_statut', table_name='equipements')
    op.drop_index('ix_equipements_type_equipement', table_name='equipements')
    op.drop_index('ix_equipements_code_interne', table_name='equipements')
    op.drop_index('ix_equipements_numero_serie', table_name='equipements')
    
    # Drop columns
    op.drop_column('equipements', 'contrat_id')
    op.drop_column('equipements', 'client_id')
    op.drop_column('equipements', 'updated_at')
    op.drop_column('equipements', 'created_at')
    op.drop_column('equipements', 'date_fin_garantie')
    op.drop_column('equipements', 'date_mise_en_service')
    op.drop_column('equipements', 'date_acquisition')
    op.drop_column('equipements', 'cout_acquisition')
    op.drop_column('equipements', 'duree_garantie_mois')
    op.drop_column('equipements', 'frequence_entretien_jours')
    op.drop_column('equipements', 'poids')
    op.drop_column('equipements', 'puissance')
    op.drop_column('equipements', 'specifications_techniques')
    op.drop_column('equipements', 'description')
    op.drop_column('equipements', 'criticite')
    op.drop_column('equipements', 'statut')
    op.drop_column('equipements', 'zone')
    op.drop_column('equipements', 'etage')
    op.drop_column('equipements', 'batiment')
    op.drop_column('equipements', 'modele')
    op.drop_column('equipements', 'marque')
    op.drop_column('equipements', 'type_equipement')
    op.drop_column('equipements', 'code_interne')
    op.drop_column('equipements', 'numero_serie')

"""sync schema with current models

Revision ID: 8cafe646bd2e
Revises: df44b376bc8a
Create Date: 2025-09-07 18:44:29.437618

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8cafe646bd2e"
down_revision: Union[str, Sequence[str], None] = "df44b376bc8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM types first
    op.execute(
        """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statutequipement') THEN
            CREATE TYPE statutequipement AS ENUM (
                'operationnel', 'maintenance', 'panne', 'retire'
            );
        END IF;
    END$$;
    """
    )

    op.execute(
        """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'criticiteequipement') THEN
            CREATE TYPE criticiteequipement AS ENUM (
                'critique', 'important', 'standard', 'non_critique'
            );
        END IF;
    END$$;
    """
    )

    # Add missing columns to equipements table
    op.add_column(
        "equipements", sa.Column("numero_serie", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("code_interne", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("marque", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("modele", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("batiment", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("etage", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("zone", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "equipements",
        sa.Column(
            "statut",
            postgresql.ENUM(
                "operationnel",
                "maintenance",
                "panne",
                "retire",
                name="statutequipement",
            ),
            nullable=False,
            server_default="operationnel",
        ),
    )
    op.add_column(
        "equipements",
        sa.Column(
            "criticite",
            postgresql.ENUM(
                "critique",
                "important",
                "standard",
                "non_critique",
                name="criticiteequipement",
            ),
            nullable=False,
            server_default="standard",
        ),
    )
    op.add_column("equipements", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "equipements", sa.Column("specifications_techniques", sa.Text(), nullable=True)
    )
    op.add_column(
        "equipements",
        sa.Column("puissance", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "equipements",
        sa.Column("poids", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "equipements",
        sa.Column("frequence_entretien_jours", sa.Integer(), nullable=True),
    )
    op.add_column(
        "equipements", sa.Column("duree_garantie_mois", sa.Integer(), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("cout_acquisition", sa.Integer(), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("date_acquisition", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("date_mise_en_service", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "equipements", sa.Column("date_fin_garantie", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "equipements",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        "equipements",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column("equipements", sa.Column("client_id", sa.Integer(), nullable=True))
    op.add_column("equipements", sa.Column("contrat_id", sa.Integer(), nullable=True))

    # Rename columns to match model
    op.alter_column("equipements", "type", new_column_name="type_equipement")
    op.alter_column(
        "equipements",
        "frequence_entretien",
        new_column_name="frequence_entretien_old",
        nullable=True,
    )
    op.execute(
        "UPDATE equipements SET frequence_entretien_jours = "
        "CAST(frequence_entretien_old AS INTEGER) WHERE "
        "frequence_entretien_old ~ '^[0-9]+$'"
    )
    op.drop_column("equipements", "frequence_entretien_old")

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_equipements_client_id",
        "equipements",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_equipements_contrat_id",
        "equipements",
        "contrats",
        ["contrat_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create indexes for better performance
    op.create_index("idx_equipement_numero_serie", "equipements", ["numero_serie"])
    op.create_index("idx_equipement_code_interne", "equipements", ["code_interne"])
    op.create_index(
        "idx_equipement_type_localisation",
        "equipements",
        ["type_equipement", "localisation"],
    )
    op.create_index(
        "idx_equipement_statut_criticite", "equipements", ["statut", "criticite"]
    )
    op.create_index(
        "idx_equipement_client_statut", "equipements", ["client_id", "statut"]
    )
    op.create_index(
        "idx_equipement_created_type", "equipements", ["created_at", "type_equipement"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_equipement_created_type", table_name="equipements")
    op.drop_index("idx_equipement_client_statut", table_name="equipements")
    op.drop_index("idx_equipement_statut_criticite", table_name="equipements")
    op.drop_index("idx_equipement_type_localisation", table_name="equipements")
    op.drop_index("idx_equipement_code_interne", table_name="equipements")
    op.drop_index("idx_equipement_numero_serie", table_name="equipements")

    # Drop foreign keys
    op.drop_constraint("fk_equipements_contrat_id", "equipements", type_="foreignkey")
    op.drop_constraint("fk_equipements_client_id", "equipements", type_="foreignkey")

    # Drop columns
    op.drop_column("equipements", "contrat_id")
    op.drop_column("equipements", "client_id")
    op.drop_column("equipements", "updated_at")
    op.drop_column("equipements", "created_at")
    op.drop_column("equipements", "date_fin_garantie")
    op.drop_column("equipements", "date_mise_en_service")
    op.drop_column("equipements", "date_acquisition")
    op.drop_column("equipements", "cout_acquisition")
    op.drop_column("equipements", "duree_garantie_mois")
    op.drop_column("equipements", "frequence_entretien_jours")
    op.drop_column("equipements", "poids")
    op.drop_column("equipements", "puissance")
    op.drop_column("equipements", "specifications_techniques")
    op.drop_column("equipements", "description")
    op.drop_column("equipements", "criticite")
    op.drop_column("equipements", "statut")
    op.drop_column("equipements", "zone")
    op.drop_column("equipements", "etage")
    op.drop_column("equipements", "batiment")
    op.drop_column("equipements", "modele")
    op.drop_column("equipements", "marque")
    op.drop_column("equipements", "code_interne")
    op.drop_column("equipements", "numero_serie")

    # Rename back
    op.alter_column("equipements", "type_equipement", new_column_name="type")
    op.add_column(
        "equipements", sa.Column("frequence_entretien", sa.String(), nullable=True)
    )

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS criticiteequipement")
    op.execute("DROP TYPE IF EXISTS statutequipement")

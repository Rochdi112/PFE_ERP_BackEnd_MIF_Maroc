from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

import sys
import os

# Ajouter le chemin racine du projet pour les imports "app.*"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Alembic Config
config = context.config

# Configurer le logger
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importer Base et les modèles pour que Alembic détecte les changements
from app.db.database import Base
from app import models  # important : charge tous les modèles
# Tu peux aussi les lister explicitement si nécessaire :
# from app.models import user, technicien, equipement, intervention, document, notification, historique

# Fournir à Alembic le metadata pour autogenerate
target_metadata = Base.metadata

# Permettre la surcharge de l'URL DB via la variable d'environnement DATABASE_URL
db_url_env = os.getenv("DATABASE_URL")
if db_url_env:
    config.set_main_option("sqlalchemy.url", db_url_env)


def run_migrations_offline() -> None:
    """Exécuter les migrations en mode 'offline' (sans DB connectée)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécuter les migrations en mode 'online' (avec DB connectée)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Activer le mode batch pour SQLite afin de supporter ALTER TABLE (op.alter_column, etc.)
        render_as_batch = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # utile si tu veux détecter les changements de type de colonnes
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# app/db/database.py

import sys
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import NoSuchModuleError, OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Initialisation de Base
Base = declarative_base()

# URL principale construite depuis les settings
DATABASE_URL = settings.DATABASE_URL


def _create_default_engine():
    """
    Crée l'engine de base de données.
    - Tente PostgreSQL (prod/dev).
    - En cas d'indisponibilité du driver (psycopg2 non installé),
      bascule sur SQLite en mémoire.
    Ce fallback évite l'échec d'import lors des tests qui remplacent get_db.
    """
    # En mode test (pytest), on force SQLite en mémoire pour isolation/rapidité
    if "pytest" in sys.modules:
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    try:
        eng = create_engine(DATABASE_URL)
    except (NoSuchModuleError, ModuleNotFoundError, ImportError) as exc:
        print(
            "Creation de l'engine Postgres impossible (driver manquant), "
            "fallback SQLite memoire: "
            f"{getattr(exc, 'msg', str(exc))}"
        )
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    except Exception as exc:
        # Toute autre erreur de création doit être remontée pour faciliter le debug
        print(
            "Creation de l'engine Postgres impossible: "
            f"{getattr(exc, 'msg', str(exc))}"
        )
        raise

    # Vérifie la connectivité sans casser l'initialisation : en cas d'échec on
    # conserve tout de même l'engine Postgres afin que l'erreur se produise lors
    # de l'utilisation effective (comportement attendu par plusieurs tests).
    try:
        with eng.connect() as _:
            pass
    except OperationalError as exc:
        print(
            "Connexion PostgreSQL indisponible (engine conservé): "
            f"{getattr(exc, 'orig', exc)}"
        )
    except Exception as exc:
        print(
            "Verification de l'engine Postgres échouée (engine conservé): "
            f"{getattr(exc, 'msg', str(exc))}"
        )
    return eng


engine = _create_default_engine()

_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialisation paresseuse du schéma en mode SQLite mémoire
_schema_initialized = False

# Assure le schéma si des tests utilisent directement SessionLocal sans
# passer par get_db
if engine.url.get_backend_name() == "sqlite":
    try:
        # Import des modèles pour enregistrer toutes les tables
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        _schema_initialized = True
    except Exception as exc:
        print(f"Initialisation immédiate du schéma SQLite échouée: {exc}")


def get_db() -> Generator[Session, None, None]:
    global _schema_initialized
    # Crée le schéma si on est en SQLite mémoire et pas encore initialisé
    if engine.url.get_backend_name() == "sqlite" and not _schema_initialized:
        try:
            # Import des modèles pour que toutes les tables soient enregistrées
            Base.metadata.create_all(bind=engine)
            _schema_initialized = True
        except Exception as exc:
            print(f"Initialisation du schéma SQLite échouée: {exc}")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fournit une session tout en garantissant le schéma en mode SQLite mémoire
def SessionLocal() -> Session:
    global _schema_initialized
    if engine.url.get_backend_name() == "sqlite":
        try:
            # create_all avec checkfirst garantit la présence des tables
            Base.metadata.create_all(bind=engine)
            _schema_initialized = True
        except Exception as exc:
            print(f"Initialisation à la volée du schéma SQLite échouée: {exc}")
    return _SessionFactory()

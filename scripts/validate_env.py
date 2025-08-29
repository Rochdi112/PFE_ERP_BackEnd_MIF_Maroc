#!/usr/bin/env python3
"""
🔧 Script de validation d'environnement pour ERP MIF Maroc
Vérifie que tous les prérequis sont présents avant de lancer les tests.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Vérifie la version de Python."""
    print("🐍 Vérification de la version Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Version trop ancienne (requis: 3.11+)")
        return False


def check_env_file():
    """Vérifie la présence du fichier .env."""
    print("📋 Vérification du fichier .env...")
    env_path = Path(".env")
    if env_path.exists():
        print("✅ Fichier .env trouvé")
        return True
    else:
        print("❌ Fichier .env manquant")
        print("💡 Créez un fichier .env basé sur .env.example")
        return False


def check_database_connection():
    """Teste la connexion à PostgreSQL."""
    print("🗄️ Test de connexion à PostgreSQL...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_SERVER", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "erp_db"),
            user=os.getenv("POSTGRES_USER", "erp_user"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )
        conn.close()
        print("✅ Connexion PostgreSQL - OK")
        return True
    except Exception as e:
        print(f"❌ Connexion PostgreSQL échouée: {e}")
        print("💡 Vérifiez que PostgreSQL est démarré et que les credentials dans .env sont corrects")
        return False


def check_dependencies():
    """Vérifie que les dépendances sont installées."""
    print("📦 Vérification des dépendances...")
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        import pytest
        print("✅ Dépendances principales - OK")
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("💡 Lancez: pip install -r requirements.txt")
        return False


def check_alembic():
    """Vérifie qu'Alembic est configuré."""
    print("🔄 Vérification d'Alembic...")
    if Path("alembic.ini").exists() and Path("app/db/migrations").exists():
        print("✅ Configuration Alembic - OK")
        return True
    else:
        print("❌ Configuration Alembic incomplète")
        return False


def run_migrations():
    """Lance les migrations Alembic."""
    print("🚀 Lancement des migrations...")
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migrations appliquées avec succès")
            return True
        else:
            print(f"❌ Erreur lors des migrations: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Impossible de lancer les migrations: {e}")
        return False


def main():
    """Fonction principale de validation."""
    print("🔧 === Validation de l'environnement ERP MIF Maroc ===\n")
    
    checks = [
        ("Version Python", check_python_version),
        ("Fichier .env", check_env_file),
        ("Dépendances", check_dependencies),
        ("Configuration Alembic", check_alembic),
        ("Connexion PostgreSQL", check_database_connection),
        ("Migrations", run_migrations),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            success = check_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Erreur lors de {name}: {e}")
            results.append((name, False))
        print()  # Ligne vide entre les checks
    
    # Résumé final
    print("📊 === RÉSUMÉ ===")
    all_passed = True
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Environnement prêt ! Vous pouvez lancer les tests avec:")
        print("   pytest app/tests/ --disable-warnings -v")
        return 0
    else:
        print("\n⚠️ Certaines vérifications ont échoué.")
        print("   Corrigez les problèmes avant de lancer les tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

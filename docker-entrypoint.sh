#!/bin/bash
# docker-entrypoint.sh - Script d'initialisation pour conteneur production

set -e

echo "🚀 Démarrage ERP MIF Maroc Backend..."

# Variables d'environnement avec valeurs par défaut
DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:password@db:5432/erp_db"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Attendre que la base de données soit disponible
echo "⏳ Attente de la base de données..."
max_attempts=30
attempt=1

until pg_isready -h $(echo $DATABASE_URL | sed -n 's|.*://[^:]*:[^@]*@\([^:]*\):.*|\1|p') -p $(echo $DATABASE_URL | sed -n 's|.*://[^:]*:[^@]*@[^:]*:\([0-9]*\)/.*|\1|p') 2>/dev/null; do
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Impossible de se connecter à la base de données après $max_attempts tentatives"
        exit 1
    fi
    echo "   Tentative $attempt/$max_attempts..."
    sleep 2
    attempt=$((attempt + 1))
done

echo "✅ Base de données disponible"

# Exécuter les migrations Alembic
echo "🔄 Exécution des migrations de base de données..."
if alembic upgrade head; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "❌ Erreur lors des migrations"
    exit 1
fi

# Générer les clés JWT si non présentes et en mode production
if [ "$ENVIRONMENT" = "production" ] && [ ! -f "keys/jwt_private.pem" ]; then
    echo "🔐 Génération des clés JWT pour la production..."
    python scripts/generate_jwt_keys.py
fi

# Créer les dossiers nécessaires
mkdir -p logs static/uploads

# Vérifier les variables d'environnement critiques
echo "🔍 Vérification de la configuration..."

critical_vars=("SECRET_KEY" "DATABASE_URL")
for var in "${critical_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Variable d'environnement manquante: $var"
        exit 1
    fi
done

# Vérifier la connectivité de la base
echo "🔗 Test de connectivité à la base de données..."
if python -c "
import sys
sys.path.append('/app')
from app.db.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1').fetchone()
        print('✅ Connexion DB réussie')
except Exception as e:
    print(f'❌ Erreur DB: {e}')
    sys.exit(1)
"; then
    echo "✅ Connectivité DB confirmée"
else
    echo "❌ Problème de connectivité DB"
    exit 1
fi

# Afficher les informations de démarrage
echo "📊 Configuration du conteneur:"
echo "   - Environment: $ENVIRONMENT"
echo "   - Log Level: $LOG_LEVEL"
echo "   - Python Path: $(which python)"
echo "   - Gunicorn Workers: ${GUNICORN_WORKERS:-4}"
echo "   - Working Directory: $(pwd)"

# Vérifier les permissions des fichiers
echo "🔒 Vérification des permissions..."
if [ ! -r "app/main.py" ]; then
    echo "❌ Fichier app/main.py non accessible"
    exit 1
fi

# Optionnel: Génération des données de démonstration en développement
if [ "$ENVIRONMENT" = "development" ] && [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
    echo "🌱 Génération des données de démonstration..."
    python scripts/seed_demo.py
fi

# Test rapide de l'application
echo "🧪 Test de sanité de l'application..."
if python -c "
import sys
sys.path.append('/app')
try:
    from app.main import app
    print('✅ Application importée avec succès')
except Exception as e:
    print(f'❌ Erreur import app: {e}')
    sys.exit(1)
"; then
    echo "✅ Application prête"
else
    echo "❌ Problème avec l'application"
    exit 1
fi

echo "🎯 Initialisation terminée - Démarrage du serveur..."

# Exécuter la commande passée en argument
exec "$@"
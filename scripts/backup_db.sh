#!/bin/bash
# scripts/backup_db.sh
# Script de sauvegarde PostgreSQL pour ERP MIF Maroc

set -e

# Configuration par défaut (peut être surchargée par variables d'environnement)
POSTGRES_HOST=${POSTGRES_HOST:-"localhost"}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-"erp_db"}
POSTGRES_USER=${POSTGRES_USER:-"erp_user"}
BACKUP_DIR=${BACKUP_DIR:-"/var/backups/postgres"}
RETENTION_DAYS=${RETENTION_DAYS:-14}

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"

# Timestamp pour le nom de fichier
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/erp_backup_${TIMESTAMP}.sql.gz"

echo "🗃️  Début de la sauvegarde PostgreSQL"
echo "📅 Date: $(date)"
echo "🏢 Base: $POSTGRES_DB"
echo "🖥️  Serveur: $POSTGRES_HOST:$POSTGRES_PORT"
echo "📁 Destination: $BACKUP_FILE"

# Sauvegarde avec compression
pg_dump -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --no-password \
        | gzip > "$BACKUP_FILE"

# Vérifier la création du fichier
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Sauvegarde créée: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "❌ Erreur: fichier de sauvegarde non créé"
    exit 1
fi

# Nettoyage des anciennes sauvegardes (> RETENTION_DAYS jours)
echo "🧹 Nettoyage des sauvegardes anciennes (>${RETENTION_DAYS} jours)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "erp_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "🗑️  $DELETED_COUNT ancien(s) fichier(s) supprimé(s)"

# Lister les sauvegardes restantes
echo "📋 Sauvegardes disponibles:"
ls -lh "$BACKUP_DIR"/erp_backup_*.sql.gz 2>/dev/null || echo "  Aucune sauvegarde trouvée"

echo "✅ Sauvegarde terminée avec succès"
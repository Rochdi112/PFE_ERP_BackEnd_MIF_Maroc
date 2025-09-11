# Makefile pour ERP MIF Maroc Backend
# Utilisation: make <command>

.PHONY: help install test test-cov lint format clean serve migrate seed report validate db-up db-down db-logs docker-build docker-run docker-down ci

# 📋 Help - Affiche les commandes disponibles
help:
	@echo "🚦 ERP MIF Maroc - Commandes disponibles:"
	@echo ""
	@echo "📦 Installation et setup:"
	@echo "  make install     - Installe les dépendances"
	@echo "  make validate    - Valide l'environnement"
	@echo ""
	@echo "🗄️ Base de données:"
	@echo "  make migrate     - Lance les migrations Alembic"
	@echo "  make seed        - Charge les données de test"
	@echo ""
	@echo "🧪 Tests et qualité:"
	@echo "  make test        - Lance les tests simples"
	@echo "  make test-cov    - Lance les tests avec couverture"
	@echo "  make lint        - Vérifie la qualité du code"
	@echo "  make format      - Formate le code (Black + isort)"
	@echo "  make report      - Génère un rapport complet"
	@echo ""
	@echo "🚀 Développement:"
	@echo "  make serve       - Lance le serveur de développement"
	@echo "  make clean       - Nettoie les fichiers temporaires"

# 📦 Installation des dépendances
install:
	@echo "📦 Installation des dépendances..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Installation terminée"

# 🔧 Validation de l'environnement
validate:
	@echo "🔧 Validation de l'environnement..."
	python validate_env.py

# 🗄️ Migrations de base de données
migrate:
	@echo "🗄️ Lancement des migrations..."
	docker compose up -d db
	alembic upgrade head

# 🌱 Chargement des données de test
seed:
	@echo "🌱 Chargement des données de test..."
	python app/seed/seed_data.py

# 🧪 Tests simples
test:
	@echo "🧪 Lancement des tests..."
	pytest app/tests/ --disable-warnings -v

# 📊 Tests avec couverture
test-cov:
	@echo "📊 Tests avec couverture de code..."
	pytest app/tests/ --cov=app --cov-report=term --cov-report=html:htmlcov -v

# 🎨 Vérification de la qualité du code
lint:
	@echo "🎨 Vérification de la qualité du code..."
	black --check app/
	isort --check-only app/
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503

# ✨ Formatage automatique du code
format:
	@echo "✨ Formatage du code..."
	black app/
	isort app/
	@echo "✅ Code formaté"

# 📊 Génération de rapport complet
report:
	@echo "📊 Génération du rapport de qualité..."
	python generate_report.py

# 🚀 Lancement du serveur de développement
serve:
	@echo "🚀 Démarrage du serveur FastAPI..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 🧹 Nettoyage des fichiers temporaires
clean:
	@echo "🧹 Nettoyage des fichiers temporaires..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/ reports/ temp/ 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

# 🐳 Commandes Docker
docker-build:
	@echo "🐳 Construction de l'image Docker..."
	docker build -t erp-backend .

docker-run:
	@echo "🐳 Lancement avec Docker Compose..."
	docker compose up --build

docker-down:
	@echo "🐳 Arrêt des conteneurs..."
	docker compose down

db-up:
	@echo "🐘 Démarrage de Postgres (docker compose)..."
	docker compose up -d db

db-down:
	@echo "🐘 Arrêt de Postgres..."
	docker compose stop db || true

db-logs:
	@echo "📜 Logs Postgres... (Ctrl+C pour quitter)"
	docker compose logs -f db

# 🔄 Pipeline complet (comme en CI/CD)
ci:
	@echo "🔄 Pipeline CI/CD local..."
	make validate
	make migrate
	make test-cov
	make lint
	make report
	@echo "🎉 Pipeline terminé !"

# 💾 Sauvegarde de base de données
backup:
	@echo "💾 Création de la sauvegarde PostgreSQL..."
	./scripts/backup_postgres.sh
	@echo "✅ Sauvegarde terminée"

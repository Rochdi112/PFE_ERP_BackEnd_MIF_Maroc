# 🚀 ERP MIF Maroc — Backend FastAPI

<p align="center">
  <em>Système de gestion des interventions industrielles</em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue.svg"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.116-009688.svg"></a>
  <a href="https://www.sqlalchemy.org/"><img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-red.svg"></a>
  <a href="https://www.postgresql.org/"><img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791.svg"></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED.svg"></a>
  <a href="#api-documentation"><img alt="OpenAPI" src="https://img.shields.io/badge/OpenAPI-3.0-green.svg"></a>
  <a href="https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc/actions"><img alt="Tests" src="https://img.shields.io/badge/tests-passing-brightgreen.svg"></a>
  <a href="#coverage"><img alt="Coverage" src="https://img.shields.io/badge/coverage-89.24%25-orange.svg"></a>
</p>

---

## 📋 Table des matières

- [📖 Présentation](#-présentation)
- [✨ Fonctionnalités](#-fonctionnalités)
- [🏗️ Architecture](#️-architecture)
- [📁 Structure du projet](#-structure-du-projet)
- [🛠️ Technologies utilisées](#️-technologies-utilisées)
- [⚡ Démarrage rapide](#-démarrage-rapide)
- [🔧 Installation et configuration](#-installation-et-configuration)
- [🗄️ Base de données](#️-base-de-données)
- [🔗 API Documentation](#-api-documentation)
- [🧪 Tests](#-tests)
- [🚀 Déploiement](#-déploiement)
- [🔒 Sécurité](#-sécurité)
- [📊 Monitoring](#-monitoring)
- [🛠️ Développement](#️-développement)
- [❓ Dépannage](#-dépannage)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

---

## 📖 Présentation

**ERP MIF Maroc** est une plateforme backend moderne et robuste développée avec **FastAPI** pour la gestion complète des interventions industrielles. Le système offre une API REST complète avec authentification JWT, contrôle d'accès basé sur les rôles (RBAC), et une architecture modulaire prête pour la production.

### 🎯 Cas d'usage

- Gestion des équipements industriels
- Planification et suivi des interventions de maintenance
- Gestion des techniciens et ressources
- Système de notifications automatiques
- Gestion documentaire et uploads de fichiers
- Rapports et analytics

---

## ✨ Fonctionnalités

### 🔐 Authentification & Autorisation
- **JWT Authentication** avec tokens d'accès et de rafraîchissement
- **RBAC (Role-Based Access Control)** avec 4 rôles :
  - `admin` : Accès complet au système
  - `responsable` : Gestion des interventions et techniciens
  - `technicien` : Exécution des interventions
  - `client` : Accès limité aux interventions liées
- **Sécurisation des mots de passe** avec bcrypt

### 👥 Gestion des utilisateurs
- CRUD complet des utilisateurs
- Gestion des profils et rôles
- Authentification par email/username
- Changement de mot de passe sécurisé

### 🔧 Gestion des équipements
- Catalogue des équipements industriels
- Suivi des fréquences de maintenance
- Localisation et type d'équipement
- Historique des interventions

### 👨‍🔧 Gestion des techniciens
- Profils des techniciens
- Compétences et spécialisations
- Disponibilité et planning
- Affectation aux interventions

### 📋 Gestion des interventions
- Création et suivi des interventions
- Statuts : `ouverte`, `en_cours`, `cloturee`, `annulee`
- Priorités : `normale`, `haute`, `critique`
- Types : `corrective`, `preventive`, `curative`
- Dates limites et urgences

### 📅 Planification
- Planning automatisé des interventions
- Génération de tâches planifiées
- Notifications de rappel
- Optimisation des ressources

### 📄 Gestion documentaire
- Upload et stockage de documents
- Association aux interventions
- Téléchargement sécurisé
- Gestion des pièces jointes

### 🔔 Notifications
- Système de notifications en temps réel
- Notifications par email
- Templates personnalisables
- Historique des notifications

### 📊 Rapports & Analytics
- Génération de rapports
- Statistiques d'intervention
- KPIs et métriques
- Export de données

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Monitoring    │
│   (React/Vue)   │◄──►│   (FastAPI)     │◄──►│   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Services      │    │   Database      │    │   Cache/Queue   │
│   Layer         │◄──►│   (PostgreSQL)  │◄──►│   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Email Service │    │   Scheduler     │
│   (Local/Disk)  │    │   (SMTP)        │    │   (APScheduler) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🏛️ Architecture technique

- **API Layer** : FastAPI avec OpenAPI 3.0
- **Business Logic** : Services modulaires
- **Data Layer** : SQLAlchemy ORM avec migrations Alembic
- **Security** : JWT + RBAC + CORS
- **Background Jobs** : APScheduler pour les tâches planifiées
- **File Storage** : Système d'upload local avec accès statique
- **Notifications** : FastAPI-Mail pour les emails
- **Monitoring** : Endpoints de santé et métriques

---

## 📁 Structure du projet

```
FastApi_ERP_BackEnd_MIF_Maroc/
├── app/                          # Code source principal
│   ├── main.py                   # Application FastAPI principale
│   ├── core/                     # Configuration et utilitaires core
│   │   ├── config.py            # Configuration Pydantic
│   │   ├── security.py          # Utilitaires de sécurité JWT
│   │   ├── rbac.py             # Contrôle d'accès basé sur les rôles
│   │   ├── exceptions.py       # Exceptions personnalisées
│   │   └── logging.py          # Configuration des logs
│   ├── api/v1/                 # Endpoints API version 1
│   │   ├── auth.py            # Authentification
│   │   ├── users.py           # Gestion des utilisateurs
│   │   ├── techniciens.py     # Gestion des techniciens
│   │   ├── equipements.py     # Gestion des équipements
│   │   ├── interventions.py   # Gestion des interventions
│   │   ├── planning.py        # Planification
│   │   ├── documents.py       # Gestion documentaire
│   │   ├── notifications.py   # Notifications
│   │   ├── filters.py         # Filtres et recherche
│   │   ├── dashboard.py       # Tableau de bord
│   │   └── health.py          # Santé du système
│   ├── db/                    # Configuration base de données
│   │   ├── database.py        # Engine SQLAlchemy
│   │   └── init_db.py         # Initialisation DB
│   ├── models/                # Modèles SQLAlchemy
│   │   ├── user.py           # Modèle utilisateur
│   │   ├── technicien.py     # Modèle technicien
│   │   ├── equipement.py     # Modèle équipement
│   │   ├── intervention.py   # Modèle intervention
│   │   ├── document.py       # Modèle document
│   │   ├── notification.py   # Modèle notification
│   │   ├── planning.py       # Modèle planning
│   │   ├── historique.py     # Historique
│   │   ├── contrat.py        # Contrats
│   │   ├── stock.py          # Gestion du stock
│   │   ├── report.py         # Rapports
│   │   └── client.py         # Clients
│   ├── schemas/              # Schémas Pydantic
│   │   ├── user.py           # Schémas utilisateur
│   │   ├── technicien.py     # Schémas technicien
│   │   ├── equipement.py     # Schémas équipement
│   │   ├── intervention.py   # Schémas intervention
│   │   └── ...               # Autres schémas
│   ├── services/             # Logique métier
│   │   ├── auth_service.py   # Service d'authentification
│   │   ├── user_service.py   # Service utilisateurs
│   │   ├── equipement_service.py # Service équipements
│   │   ├── intervention_service.py # Service interventions
│   │   ├── technicien_service.py # Service techniciens
│   │   ├── document_service.py # Service documents
│   │   ├── notification_service.py # Service notifications
│   │   └── planning_service.py # Service planning
│   ├── tasks/                # Tâches planifiées
│   │   ├── scheduler.py      # Configuration scheduler
│   │   ├── notification_tasks.py # Tâches de notification
│   │   └── init.py           # Initialisation
│   ├── seed/                 # Données de démonstration
│   │   └── seed_data.py      # Script de seed
│   └── static/               # Fichiers statiques
│       └── uploads/          # Uploads utilisateurs
├── templates/                # Templates email
│   ├── notification_affectation.html
│   ├── notification_alerte.html
│   ├── notification_cloture.html
│   └── notification_information.html
├── tests/                    # Tests unitaires et d'intégration
│   ├── conftest.py          # Configuration des tests
│   ├── api/                 # Tests API
│   ├── unit/                # Tests unitaires
│   └── integration/         # Tests d'intégration
├── scripts/                 # Scripts utilitaires
│   ├── openapi_export.py    # Export OpenAPI
│   ├── validate_env.py      # Validation environnement
│   ├── e2e_smoke.py         # Tests end-to-end
│   └── list_routes.py       # Liste des routes
├── deploy/                  # Configuration déploiement
│   └── nginx.sample.conf    # Configuration Nginx
├── monitoring/              # Monitoring
│   └── prometheus.yml       # Configuration Prometheus
├── docker-compose.yml       # Docker Compose
├── docker-compose.prod.yml  # Docker Compose production
├── Dockerfile              # Dockerfile application
├── Dockerfile.prod         # Dockerfile production
├── requirements.txt        # Dépendances Python
├── pyproject.toml          # Configuration projet
├── pytest.ini             # Configuration tests
├── alembic.ini            # Configuration Alembic
├── Makefile               # Commandes make
├── .env.example           # Exemple de configuration
└── README.md              # Documentation
```

---

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** - Framework web moderne et rapide
- **SQLAlchemy 2.0** - ORM Python pour la base de données
- **Pydantic v2** - Validation et sérialisation des données
- **Alembic** - Migrations de base de données
- **PostgreSQL** - Base de données relationnelle
- **Redis** - Cache et files d'attente

### Sécurité
- **JWT (JSON Web Tokens)** - Authentification stateless
- **bcrypt** - Hachage des mots de passe
- **CORS** - Cross-Origin Resource Sharing
- **RBAC** - Contrôle d'accès basé sur les rôles

### Outils de développement
- **Uvicorn** - Serveur ASGI haute performance
- **pytest** - Framework de tests
- **Black** - Formatage automatique du code
- **isort** - Tri automatique des imports
- **flake8** - Linting du code
- **coverage** - Analyse de couverture de code

### Déploiement
- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration des services
- **Nginx** - Reverse proxy et load balancing

### Communication
- **FastAPI-Mail** - Envoi d'emails
- **APScheduler** - Planification des tâches

---

## ⚡ Démarrage rapide

### Prérequis
- Python 3.11+
- Docker Desktop
- Git

### 🚀 Démarrage avec Docker (Recommandé)

```bash
# 1. Cloner le repository
git clone https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc.git
cd FastApi_ERP_BackEnd_MIF_Maroc

# 2. Créer le fichier .env
cp .env.example .env

# 3. Lancer avec Docker Compose
docker compose up --build -d

# 4. Vérifier que l'application fonctionne
curl http://localhost:8000/health
```

L'application sera disponible sur :
- **API** : http://localhost:8000
- **Documentation** : http://localhost:8000/docs
- **Documentation alternative** : http://localhost:8000/redoc

### 🖥️ Démarrage local (Windows PowerShell)

```powershell
# 1. Créer et activer l'environnement virtuel
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 2. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 3. Démarrer PostgreSQL avec Docker
docker compose up -d db

# 4. Appliquer les migrations
alembic upgrade head

# 5. Lancer l'application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 🛠️ Démarrage avec VS Code

Utilisez les tâches intégrées de VS Code :

1. **Python: Create venv & Install** - Crée l'environnement virtuel et installe les dépendances
2. **DB: Alembic upgrade head** - Applique les migrations de base de données
3. **Dev: Run FastAPI (reload)** - Lance l'application en mode développement

---

## 🔧 Installation et configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Sécurité
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
LOG_LEVEL=INFO

# Base de données PostgreSQL
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Email SMTP
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=user
SMTP_PASSWORD=password
EMAILS_FROM_EMAIL=no-reply@example.com

# Répertoire d'upload
UPLOAD_DIRECTORY=app/static/uploads

# CORS
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

# Scheduler
ENABLE_SCHEDULER=false
```

### Validation de la configuration

```bash
python scripts/validate_env.py
```

---

## 🗄️ Base de données

### Migrations Alembic

```bash
# Appliquer toutes les migrations
alembic upgrade head

# Créer une nouvelle migration
alembic revision --autogenerate -m "Description de la migration"

# Voir le statut des migrations
alembic current
```

### Données de démonstration

```bash
# Peupler la base avec des données de test
python -c "from app.seed.seed_data import seed_database; seed_database()"
```

---

## 🔗 API Documentation

### Endpoints principaux

| Endpoint | Méthode | Description | Authentification |
|----------|---------|-------------|------------------|
| `/health` | GET | État de santé du système | Non requis |
| `/auth/token` | POST | Authentification JWT | Non requis |
| `/auth/me` | GET | Profil utilisateur connecté | Requis |
| `/users/` | GET/POST | Gestion des utilisateurs | Admin requis |
| `/equipements/` | GET/POST | Gestion des équipements | Requis |
| `/interventions/` | GET/POST | Gestion des interventions | Requis |
| `/techniciens/` | GET/POST | Gestion des techniciens | Requis |
| `/documents/` | POST | Upload de documents | Requis |
| `/notifications/` | GET/POST | Gestion des notifications | Requis |

### Documentation interactive

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Export OpenAPI

```bash
# Export complet (recommandé)
python scripts/openapi_export_runtime.py

# Export approximatif (fallback)
python scripts/openapi_export.py
```

Le fichier `openapi.json` sera généré à la racine du projet.

---

## 🧪 Tests

### Exécution des tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/api/test_auth_api.py
pytest tests/unit/test_models.py

# Tests en mode verbose
pytest -v
```

### Couverture de code

Le projet maintient une couverture de code supérieure à **80%** :

- **Couverture actuelle** : 89.24%
- **Rapport HTML** : `htmlcov/index.html`
- **Rapport XML** : `coverage.xml`

### Structure des tests

```
tests/
├── conftest.py              # Configuration commune
├── api/                     # Tests d'API
│   ├── test_auth_api.py
│   ├── test_users_api.py
│   ├── test_equipements_api.py
│   └── ...
├── unit/                    # Tests unitaires
│   ├── test_services.py
│   ├── test_models.py
│   └── ...
└── integration/             # Tests d'intégration
    └── test_workflows.py
```

---

## 🚀 Déploiement

### Production avec Docker

```bash
# Build et déploiement
docker compose -f docker-compose.prod.yml up --build -d

# Vérification
docker compose -f docker-compose.prod.yml logs -f
```

### Configuration Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Variables d'environnement production

```env
ENV=production
SECRET_KEY=your-production-secret-key
POSTGRES_HOST=your-production-db-host
POSTGRES_PASSWORD=your-production-db-password
CORS_ALLOW_ORIGINS=["https://your-frontend-domain.com"]
```

---

## 🔒 Sécurité

### Authentification JWT

```python
# Exemple d'utilisation
import httpx

# Obtenir un token
response = httpx.post("http://localhost:8000/auth/token", data={
    "username": "admin@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Utiliser le token
headers = {"Authorization": f"Bearer {token}"}
response = httpx.get("http://localhost:8000/users/me", headers=headers)
```

### Contrôle d'accès

Le système implémente un contrôle d'accès basé sur les rôles :

- **Public** : `/health`, `/docs`, `/auth/token`
- **Authentifié** : Profil utilisateur, interventions liées
- **Technicien** : Modification du statut des interventions
- **Responsable** : Gestion des techniciens et équipements
- **Admin** : Accès complet au système

### Bonnes pratiques de sécurité

- Mots de passe hashés avec bcrypt
- Tokens JWT avec expiration
- Validation des entrées avec Pydantic
- Protection contre les attaques CSRF
- Headers de sécurité CORS configurés
- Logs d'audit des actions sensibles

---

## 📊 Monitoring

### Endpoints de santé

```bash
# Santé basique
GET /health
# {"status": "ok", "timestamp": "2025-08-29T19:00:00Z", "service": "ERP MIF Maroc"}

# Santé détaillée
GET /health/detailed
# Informations complètes sur la DB, cache, système

# Métriques Prometheus
GET /metrics
# Métriques système et applicatives
```

### Configuration Prometheus

```yaml
scrape_configs:
  - job_name: 'erp-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Logs

Les logs sont configurés avec des niveaux personnalisables :

- **DEBUG** : Informations détaillées pour le développement
- **INFO** : Informations générales sur le fonctionnement
- **WARNING** : Avertissements sur des problèmes potentiels
- **ERROR** : Erreurs qui ne bloquent pas l'application
- **CRITICAL** : Erreurs critiques

---

## 🛠️ Développement

### Commandes utiles

```bash
# Installation des dépendances
make install

# Validation de l'environnement
make validate

# Migration de la base de données
make migrate

# Lancement du serveur
make serve

# Formatage du code
make format

# Linting
make lint

# Génération de rapport
make report

# Build Docker
make docker-build

# Lancement Docker
make docker-run
```

### Qualité du code

Le projet utilise plusieurs outils pour maintenir la qualité du code :

- **Black** : Formatage automatique
- **isort** : Tri des imports
- **flake8** : Détection des erreurs de style
- **mypy** : Vérification des types (optionnel)

### Structure des commits

```
feat: ajout de la fonctionnalité X
fix: correction du bug Y
docs: mise à jour de la documentation
style: formatage du code
refactor: refactorisation du code
test: ajout de tests
chore: tâches de maintenance
```

---

## ❓ Dépannage

### Problèmes courants

#### 1. Erreur de connexion à la base de données

```bash
# Vérifier que PostgreSQL est démarré
docker compose ps

# Redémarrer la base de données
docker compose restart db

# Vérifier les logs
docker compose logs db
```

#### 2. Erreur lors des migrations Alembic

```bash
# En local, s'assurer que PostgreSQL est accessible
docker compose up -d db

# Vérifier la connexion
python -c "from app.db.database import engine; print('Connexion OK' if engine else 'Erreur')"

# Réinitialiser les migrations si nécessaire
alembic downgrade base
alembic upgrade head
```

#### 3. Problèmes d'upload de fichiers

```bash
# Vérifier les permissions du répertoire
ls -la app/static/uploads/

# Créer le répertoire s'il n'existe pas
mkdir -p app/static/uploads

# Vérifier la configuration
python -c "from app.core.config import settings; print(settings.UPLOAD_DIRECTORY)"
```

#### 4. Erreurs CORS

```bash
# Vérifier la configuration CORS
python -c "from app.core.config import settings; print(settings.CORS_ALLOW_ORIGINS)"

# Ajouter l'origine du frontend si nécessaire
# Dans .env : CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

#### 5. Tests qui échouent

```bash
# Nettoyer l'environnement de test
docker compose down -v

# Redémarrer les services
docker compose up -d db

# Relancer les tests
pytest -v
```

### Logs de débogage

```bash
# Logs de l'application
docker compose logs app

# Logs avec suivi en temps réel
docker compose logs -f app

# Logs de la base de données
docker compose logs db
```

---

## 🤝 Contribution

### Processus de contribution

1. **Fork** le projet
2. **Clone** votre fork : `git clone https://github.com/your-username/FastApi_ERP_BackEnd_MIF_Maroc.git`
3. **Créez** une branche : `git checkout -b feature/nouvelle-fonctionnalite`
4. **Commitez** vos changements : `git commit -m 'feat: ajout de la fonctionnalité X'`
5. **Poussez** vers votre fork : `git push origin feature/nouvelle-fonctionnalite`
6. **Créez** une Pull Request

### Standards de code

- Respecter PEP 8
- Utiliser des types hints
- Écrire des tests pour les nouvelles fonctionnalités
- Maintenir une couverture de code > 80%
- Documenter les fonctions complexes

### Tests requis

Avant de soumettre une PR :

```bash
# Lancer tous les tests
pytest

# Vérifier la couverture
pytest --cov=app --cov-report=term-missing

# Tests de linting
make lint

# Formatage du code
make format
```

---

## 📄 Licence

**© 2025 MIF Maroc — Tous droits réservés**

Ce projet est développé par **MIF Maroc** pour la gestion des interventions industrielles.

### Conditions d'utilisation

- Usage interne autorisé pour MIF Maroc
- Modification et distribution soumises à autorisation
- Contact : [contact@mif-maroc.com](mailto:contact@mif-maroc.com)

---

## 📞 Support

Pour toute question ou problème :

- **Documentation** : [README.md](README.md)
- **Issues** : [GitHub Issues](https://github.com/Rochdi112/FastApi_ERP_BackEnd_MIF_Maroc/issues)
- **Email** : support@mif-maroc.com

---

<p align="center">
  <em>Rochdi Sabir</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-FastAPI-009688.svg" alt="Made with FastAPI">
  <img src="https://img.shields.io/badge/Powered%20by-SQLAlchemy-red.svg" alt="Powered by SQLAlchemy">
  <img src="https://img.shields.io/badge/Hosted%20on-Docker-2496ED.svg" alt="Hosted on Docker">
</p>

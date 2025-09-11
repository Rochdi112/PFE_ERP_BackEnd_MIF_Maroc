Audit Go‑Prod – ERP MIF Maroc
Objectif et contexte

Objectif : ce document décrit toutes les étapes, correctifs et configurations nécessaires pour passer le backend ERP MIF Maroc d’un état fonctionnel mais non conforme aux exigences de production vers une solution prête pour la mise en production (Go‑Prod).

Contexte : le backend actuel est une application FastAPI exposant des routes REST versionnées (/api/v1/*) avec authentification JWT, gestion des utilisateurs, équipements, techniciens et interventions, planification, notifications et tableau de bord. Un audit technique a été réalisé ; il a montré une architecture claire avec des services, un ORM SQLAlchemy, des migrations Alembic, des tests (> 90 % de couverture) et des métriques Prometheus. L’audit a cependant mis en évidence des lacunes critiques : absence de refresh tokens, durée de vie des tokens d’accès trop longue, CORS permissif, aucune politique de mot de passe, absence de chiffrement des documents, pas de limitation de débit, aucune sauvegarde de la base de données, absence de CI/CD et de tests de performance. Ce document rassemble les correctifs à mettre en œuvre, propose une infrastructure de déploiement et détaille le plan d’action pour atteindre un Go‑Prod.

Executive summary Go‑Prod
Forces de la solution

Architecture modulaire : découpage clair par domaines (API, services, modèles, schémas, tâches planifiées).

ORM et migrations : SQLAlchemy et Alembic assurent un schéma de base de données versionné.

Tests complets : couverture > 90 % des lignes et scénario d’intégration couvrant CRUD, RBAC, notifications et planning.

Fonctionnalités métier : gestion des rôles (admin, responsable, technicien, client), interventions avec statuts/priorités, calendrier (drag & drop), notifications et tableaux de bord.

Observabilité : logs JSON structurés et métriques Prometheus exposées.

Documentation : OpenAPI 3.0 générée automatiquement et endpoints de santé (/api/v1/health).

Faiblesses critiques restantes

JWT long‑vécu et pas de refresh : le token d’accès expire au bout de 60 minutes et il n’existe pas de refresh token. Les bonnes pratiques recommandent des tokens d’accès de courte durée pour réduire la fenêtre d’attaque
auth0.com
 et l’utilisation de refresh tokens avec rotation pour éviter qu’un jeton volé soit réutilisable
auth0.com
.

CORS trop permissif : la configuration actuelle utilise l’astérisque ('*') qui permet les requêtes simples mais interdit les appels avec credentials. La documentation FastAPI précise que le wildcard ne doit pas être utilisé avec les cookies ou en-têtes d’autorisation et qu’il est préférable de spécifier explicitement les origines autorisées
fastapi.tiangolo.com
.

Politique de mot de passe inexistante : OWASP recommande un mot de passe d’au moins huit caractères combinant lettres, chiffres et symboles
security.stackexchange.com
. Rien n’impose aujourd’hui ces règles ni l’historique des mots de passe.

Chiffrement au repos des documents : les fichiers téléchargés sont stockés en clair sur le disque. Le module cryptography indique que Fernet garantit la confidentialité et l’intégrité des données chiffrées
cryptography.io
, mais il n’est pas utilisé.

Absence de scan antivirus : aucun contrôle antivirus n’est exécuté sur les fichiers uploadés.

Pas de rate‑limit : le backend n’impose aucune limitation de débit ou protection contre les attaques par force brute.

Headers sécurité incomplets : le proxy Nginx n’ajoute pas de HSTS, CSP ou autres en-têtes de sécurité.

Backups PostgreSQL absents : aucune politique de sauvegarde et de restauration n’est définie, alors que le RPO/RTO exigé est < 1 h.

CI/CD et pre‑commit manquants : aucun pipeline automatisé n’exécute les tests, le linting et les audits de sécurité. Les hooks pre‑commit (ruff, black, isort, mypy, bandit, pip‑audit) ne sont pas configurés.

SLA et tests de performance : aucune mesure de performance ne prouve que les requêtes CRUD répondent en < 2 s avec 100 utilisateurs simultanés.

Décision Go/No‑Go

La solution actuelle ne peut pas être mise en production en l’état (No‑Go). Les forces de l’architecture et des fonctionnalités montrent un produit mature, mais les faiblesses identifiées exposent à des risques de sécurité (vol de tokens, exfiltration de documents), d’indisponibilité (pas de sauvegarde), et de qualité de service (pas de tests de charge). Une mise en production est envisageable après l’implémentation des correctifs obligatoires et la validation des critères Go‑Prod.

Correctifs obligatoires avant Go‑Prod

Cette section décrit les correctifs à réaliser. Chaque correctif comprend une justification et un extrait de configuration ou de code.

JWT : durée de vie courte, refresh token et rotation

Un token d’accès court‑vécu limite la fenêtre d’attaque, tandis qu’un refresh token permet de maintenir la session sans obliger l’utilisateur à se reconnecter
auth0.com
. La rotation des refresh tokens garantit qu’à chaque utilisation, un nouveau refresh token est émis, ce qui réduit l’impact d’un jeton compromis
auth0.com
.

Réduire la durée de vie de l’access token : définir ACCESS_TOKEN_EXPIRE_MINUTES=15 dans la configuration.

Ajouter REFRESH_TOKEN_EXPIRE_DAYS : durée de validité des refresh tokens (par ex. 7 jours).

Créer un modèle SQL RefreshToken avec les champs user_id, token, expires_at, rotated, revoked (voir exemple ci‑dessous).

Services d’authentification : fonctions pour créer un refresh token, le faire tourner (rotation) et révoquer tous les refresh tokens d’un utilisateur.

Endpoints : exposer /token (login) retournant access_token et refresh_token; /refresh pour échanger un refresh token valide contre un nouveau couple; /logout pour révoquer tous les refresh tokens de l’utilisateur.

# app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# app/models/refresh_token.py
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    rotated = Column(Boolean, default=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    __table_args__ = (
        Index("ix_refresh_active", "user_id", "revoked", "rotated"),
    )

# app/services/auth_service.py (extraits)
from secrets import token_urlsafe

def create_refresh_token(db: Session, user_id: int) -> str:
    token = token_urlsafe(48)
    refresh = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh)
    db.commit()
    return token

def rotate_refresh_token(db: Session, old_token: str) -> str:
    rt = db.query(RefreshToken).filter_by(token=old_token, revoked=False, rotated=False).first()
    if not rt or rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="refresh invalid")
    rt.rotated = True
    db.commit()
    return create_refresh_token(db, rt.user_id)

def revoke_all_user_tokens(db: Session, user_id: int):
    db.query(RefreshToken).filter_by(user_id=user_id, revoked=False).update({"revoked": True})
    db.commit()

# app/api/v1/auth.py (extraits)
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # authentification …
    access = create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh = create_refresh_token(db, user.id)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.post("/refresh")
def refresh(token: str = Form(...), db: Session = Depends(get_db)):
    new_refresh = rotate_refresh_token(db, token)
    access = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}

@router.post("/logout")
@roles_required(Role.any)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    revoke_all_user_tokens(db, current_user.id)
    return {"message": "ok"}

CORS : profils production stricts

La documentation de FastAPI indique que l’utilisation de "*" comme liste d’origines n’autorise que des requêtes sans credentials et qu’il est préférable de déclarer explicitement les origines autorisées
fastapi.tiangolo.com
. Elle montre également comment configurer CORSMiddleware avec une liste d’origines, les méthodes et en‑têtes autorisés
fastapi.tiangolo.com
. De plus, il n’est pas permis de combiner allow_credentials=True avec des wildcards
fastapi.tiangolo.com
.

Pour chaque environnement, définissez une variable CORS_ALLOW_ORIGINS contenant les URL de confiance (par ex. https://erp.mif.ma en production) et configurez CORSMiddleware comme suit :

# app/main.py
from fastapi.middleware.cors import CORSMiddleware

origins = settings.CORS_ALLOW_ORIGINS if not settings.DEBUG else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

Politique de mot de passe

Selon les recommandations OWASP, les mots de passe doivent avoir une longueur minimale de huit caractères et inclure une combinaison de lettres, de chiffres et de symboles
security.stackexchange.com
. Ajoutez une fonction de validation dans app/core/security.py et appelez‑la lors de la création ou de la modification d’un mot de passe :

# app/core/security.py
from fastapi import HTTPException, status

ALLOWED_SYMBOLS = "!@#$%^&*()-_+=[]{};:,.?/|"

def validate_password_policy(password: str) -> None:
    if len(password) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password too short")
    if password.islower() or password.isupper():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mixed case required")
    if not any(c.isdigit() for c in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="digit required")
    if not any(c in ALLOWED_SYMBOLS for c in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="symbol required")

Chiffrement au repos des documents (AES/Fernet)

Les fichiers doivent être chiffrés au repos pour garantir qu’ils ne puissent pas être lus ou manipulés sans la clé. Le module Fernet du package cryptography fournit un chiffrement symétrique authentifié garantissant que le message chiffré ne peut être lu ou modifié sans la clé
cryptography.io
. Ajoutez une clé FILES_ENC_KEY générée via Fernet.generate_key() dans .env et implémentez le chiffrement/déchiffrement :

# app/services/document_service.py
from cryptography.fernet import Fernet
from app.core.config import settings

fernet = Fernet(settings.FILES_ENC_KEY.encode())

def save_document(file: UploadFile) -> str:
    raw = file.file.read()
    encrypted = fernet.encrypt(raw)
    # enregistrer encrypted sur disque ou S3
    file_path = _save_bytes_to_disk(encrypted, file.filename)
    return file_path

def read_document(file_path: str) -> bytes:
    encrypted = _read_bytes_from_disk(file_path)
    return fernet.decrypt(encrypted)

Scan antivirus optionnel (ClamAV)

Pour prévenir l’upload de fichiers malveillants, intégrez un scan ClamAV dans le service d’upload. Un conteneur ClamAV (clamd) peut être ajouté au docker‑compose. Exemple de fonction :

# app/services/antivirus.py
import subprocess
import shlex

def scan_bytes(data: bytes) -> bool:
    process = subprocess.run(shlex.split("clamdscan --stdin --no-summary"), input=data, capture_output=True)
    return process.returncode == 0


Lors de l’upload, lisez le fichier, lancez scan_bytes; refusez le téléchargement si le retour n’est pas 0.

Rate‑limit middleware

Pour atténuer les attaques par force brute et les abus d’API, ajoutez un middleware de limitation de débit utilisant Starlette ou le package slowapi. Voici un exemple simple :

# app/core/ratelimit.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from time import time
from collections import defaultdict

WINDOW = 60  # fenêtre en secondes
LIMIT = 120  # requêtes par fenêtre
_hits = defaultdict(list)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ip = request.client.host
        now = time()
        _hits[ip] = [t for t in _hits[ip] if now - t < WINDOW] + [now]
        if len(_hits[ip]) > LIMIT:
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        return await call_next(request)

# app/main.py
if settings.ENV == "production":
    app.add_middleware(RateLimitMiddleware)

Headers sécurité (Nginx)

Configurez Nginx pour ajouter les en‑têtes de sécurité suivants :

add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'";
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header Referrer-Policy strict-origin-when-cross-origin;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";


Placez cette configuration dans un fichier nginx.conf monté dans le conteneur Nginx.

Backups PostgreSQL

Créez un service de sauvegarde ou un cron pg_dump exécuté quotidiennement. Exemple de script :

#!/bin/bash
set -e
BACKUP_DIR="/var/backups/postgres"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
pg_dump -h db -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/erp_${TIMESTAMP}.sql.gz"
# supprimer les backups de plus de 14 jours
tmpwatch --mtime --all 14d "$BACKUP_DIR" || find "$BACKUP_DIR" -type f -mtime +14 -delete


Ajoutez ce script à un conteneur dédié ou exécutez‑le via un cron dans l’orchestrateur. Stockez les backups sur un stockage externe (S3/MinIO) pour respecter le RPO/RTO.

CI/CD GitHub Actions

Mettre en place des workflows GitHub Actions pour le backend et le frontend. Exemple pour le backend (.github/workflows/backend-ci.yml) :

name: Backend CI
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: erp
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
        ports: ["5432:5432"]
        options: >-
          --health-cmd="pg_isready -U user -d erp" --health-interval=10s --health-timeout=5s --health-retries=5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ruff black isort mypy pytest pytest-cov bandit pip-audit
      - name: Lint
        run: |
          black --check app
          isort --check-only app
          ruff check app
      - name: Type check
        run: mypy app
      - name: Security audit
        run: |
          bandit -r app
          pip-audit -r requirements.txt
      - name: Test
        env:
          DATABASE_URL: postgres://user:password@localhost:5432/erp
        run: pytest --cov=app --cov-report=xml


Ajoutez un workflow similaire pour le frontend (tests Jest, lint) et un autre pour la construction et le push d’images Docker (docker-build.yml). Intégrez un pipeline de déploiement (deploy.yml) si l’infrastructure cible (Kubernetes, Docker Swarm ou autre) le permet.

Tests de performance

Utilisez Locust pour simuler 100 utilisateurs simultanés sur les endpoints CRUD et vérifier que le temps de réponse p95 est < 2 s. Exemple de perf/locustfile.py :

from locust import HttpUser, task, between

class CRUDUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def create_and_read_user(self):
        # créer un utilisateur
        data = {"email": "perf@example.com", "password": "StrongPass1!"}
        self.client.post("/api/v1/users/", json=data, headers={"Authorization": f"Bearer {self.token}"})
        self.client.get("/api/v1/users/")


Lancez locust -f perf/locustfile.py --users 100 --spawn-rate 10 -H http://localhost:8000 et ajustez l’application (indexation, pooling) pour respecter les performances.

Matrice ✅/❌ après correctifs
Domaine	Exigence	Statut actuel	Statut Go‑Prod
Fonctionnelles	Auth JWT avec refresh et rotation	❌ absent	✅ implémenté (TTL 15 min, refresh tokens rotatifs)
	RBAC (admin, responsable, technicien, client)	✅	✅
	CRUD utilisateurs/équipements/techniciens/interventions	✅	✅
	Gestion documentaire sécurisée	❌ pas de chiffrement ni scan	✅ chiffré, scan antivirus optionnel
	Notifications (app & email)	✅	✅
	Planning / calendrier Drag & drop	✅	✅
	Dashboard/KPIs, export	✅	✅
Non‑fonctionnelles	Temps de réponse < 2 s, 100 users	❌ non testé	✅ testé via Locust
	CORS restrictif	❌ wildcard	✅ origines déclarées et credentials permis
	Politique de mot de passe	❌	✅ 10 caractères, mixte, validation
	Chiffrement au repos AES‑256	❌	✅ via Fernet
	Audit trail	✅	✅
	Logs JSON & métriques Prometheus	✅	✅
	Sauvegardes DB	❌	✅ script & stockage externalisé
	CI/CD automatisé	❌	✅ workflows Actions, hooks pre‑commit
	SLA 99.5 %, RTO < 4 h, RPO < 1 h	❌	✅ définis (backups + supervision)
Infrastructure & déploiement
Docker Compose complet

Un fichier docker-compose.yml peut orchestrer l’ensemble des services :

version: '3.8'
services:
  backend:
    build: .
    env_file: .env
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/erp
      - SECRET_KEY=${SECRET_KEY}
      - ACCESS_TOKEN_EXPIRE_MINUTES=15
      - REFRESH_TOKEN_EXPIRE_DAYS=7
      - CORS_ALLOW_ORIGINS=https://erp.mif.ma
      - SMTP_HOST=smtp.example.com
      - SMTP_PORT=587
      - SMTP_USER=mailer
      - SMTP_PASSWORD=********
      - FILES_ENC_KEY=${FILES_ENC_KEY}
    volumes:
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      - db
  frontend:
    build: ./frontend
    environment:
      - REACT_APP_API_URL=https://erp.mif.ma/api/v1
    ports:
      - "3000:80"
    depends_on:
      - backend
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=erp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - db_data:/var/lib/postgresql/data
  nginx:
    image: nginx:alpine
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend
  prometheus:
    image: prom/prometheus
    volumes:
      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
volumes:
  db_data:
  grafana_data:

Variables d’environnement

SECRET_KEY : clé secrète FastAPI (aléatoire).

FILES_ENC_KEY : clé Fernet pour le chiffrement des documents (générée via Fernet.generate_key()).

DATABASE_URL : URL de connexion PostgreSQL.

CORS_ALLOW_ORIGINS : liste d’origines autorisées (séparées par virgule).

SMTP_* : paramètres de messagerie pour l’envoi de notifications.

Pour le frontend : REACT_APP_API_URL pointe vers l’URL publique de l’API.

Les secrets doivent être injectés via le mécanisme GitHub Actions (secrets) ou un gestionnaire de secrets (Vault, AWS Secrets Manager).

Configuration Nginx

Un fichier nginx.conf simple peut servir de reverse proxy et ajouter les en‑têtes de sécurité. Exemple :

events { }
http {
    server {
        listen 80;
        server_name erp.mif.ma;
        include /etc/nginx/mime.types;
        # Sécurité
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'";
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header Referrer-Policy strict-origin-when-cross-origin;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";

        location / {
            proxy_pass http://frontend:80;
        }
        location /api/ {
            proxy_pass http://backend:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}

Monitoring Prometheus/Grafana

Configurez Prometheus pour scrapper le backend (endpoint /api/v1/health/metrics) et Postgres. Exemple prometheus.yml :

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /api/v1/health/metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['db:9187']


Ajoutez l’exporter postgres_exporter dans le docker-compose. Importez ensuite des dashboards Grafana pour FastAPI et PostgreSQL.

Backups et restauration

Planifier un job Cron (sur l’hôte ou dans un conteneur pgbackups) exécutant le script de sauvegarde quotidiennement. Tester régulièrement la restauration sur un environnement de pré‑production pour valider le RPO/RTO.

CI/CD et secrets

Workflows GitHub Actions : backend-ci.yml, frontend-ci.yml, docker-build.yml, deploy.yml.

Pre‑commit : configurez pre-commit avec les hooks ruff, black, isort, mypy, bandit et pip-audit.

Secrets : stocker DATABASE_URL, SECRET_KEY, FILES_ENC_KEY, SMTP_PASSWORD dans les secrets GitHub (Repository secrets ou Environment secrets).

Plan d’action 14 jours
Jour	Actions	Priorité
J1–J2	Mettre en place lint (ruff, black, isort) et typage (mypy) via pre‑commit ; réduire ACCESS_TOKEN_EXPIRE_MINUTES à 15 min ; configurer CORS_ALLOW_ORIGINS par environnement.	Haute
J3–J5	Implémenter le modèle RefreshToken, les services de création/rotation/révocation et les endpoints /refresh et /logout ; écrire des tests unitaires et d’intégration pour la rotation.	Haute
J6–J7	Générer une clé Fernet et implémenter le chiffrement/déchiffrement des documents ; ajouter un scan antivirus (ClamAV) à l’upload.	Haute
J8	Ajouter le middleware de rate‑limit et durcir les en‑têtes de sécurité dans Nginx.	Haute
J9	Mettre en place le script de sauvegarde PostgreSQL et programmer les sauvegardes quotidiennes vers un stockage externe ; vérifier la restauration.	Haute
J10–J11	Créer les workflows GitHub Actions (CI pour backend/frontend, audit sécurité, build d’images) et activer pre‑commit.	Moyenne
J12	Écrire des scénarios Locust et exécuter des tests de charge ; optimiser les requêtes lentes (indexation, requêtes N+1, pooling).	Moyenne
J13	Définir les SLO/SLA (disponibilité 99,5 %, RTO < 4 h, RPO < 1 h) et configurer les alertes (Prometheus Alertmanager).	Moyenne
J14	Réaliser un smoke test de bout en bout via docker-compose up sur un environnement de staging ; valider la checklist Go‑Prod et décider du Go.	Haute
Critères Go‑Prod

Un passage en production est validé si tous les critères suivants sont satisfaits :

Couverture de tests ≥ 80 % (unitaires et intégration).

Temps de réponse : les opérations CRUD doivent répondre en < 2 s avec 100 utilisateurs simultanés (p95) et ne présenter aucune erreur.

Authentification sécurisée : access tokens de 15 min, refresh tokens avec rotation, endpoints /refresh et /logout fonctionnels.

CORS et en‑têtes de sécurité : origines de confiance configurées, allow_credentials activé, en‑têtes HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy et Permissions-Policy appliqués.

Politique de mot de passe : validation de longueur (≥ 10 caractères), mélange de casse, chiffres et symboles.

Chiffrement des documents : utilisation d’une clé Fernet unique et stockée de façon sécurisée.

Rate‑limit : middleware actif et logs de dépassement de quota.

Sauvegardes PostgreSQL : script automatisé, stockage externe, tests de restauration réussis.

CI/CD : pipeline exécutant lint, type check, audit sécurité, tests et build d’image Docker ; déploiement automatique sur l’environnement de staging.

Monitoring : métriques disponibles dans Prometheus et dashboards Grafana opérationnels; alertes configurées sur la latence et la disponibilité.

SLA/SLO : documentés et respectés; logs d’audit et politique d’historique des interventions en place.

Annexes
Makefile

Un Makefile peut centraliser les commandes courantes :

.PHONY: run clean fmt lint mypy test cov build

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	black app && isort app

lint:
	ruff check app

mypy:
	mypy app

test:
	pytest -q

cov:
	pytest --cov=app --cov-report=term-missing

build:
	docker build -t erp-backend:latest .

Script de seed de données

Créez un script scripts/seed.py pour insérer des données initiales (rôles, priorités, utilisateurs de test) via SQLAlchemy.

Exemple de script de performance Locust
from locust import HttpUser, task, between

class UserBehavior(HttpUser):
    wait_time = between(1, 5)

    @task(2)
    def list_equipements(self):
        self.client.get("/api/v1/equipements/")

    @task(1)
    def create_intervention(self):
        data = {"equipement_id": 1, "titre": "Test", "priorite": "HAUTE", "statut": "OUVERTE"}
        self.client.post("/api/v1/interventions/", json=data, headers={"Authorization": f"Bearer {self.token}"})

Exemple de configuration prometheus.yml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /api/v1/health/metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['db:9187']
    metrics_path: /

Exemple de fichier pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/ruff
    rev: v0.1.5
    hooks:
      - id: ruff
        args: ["--fix"]
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", "app"]
  - repo: https://github.com/TrailofBits/pip-audit
    rev: v2.7.2
    hooks:
      - id: pip-audit
        additional_dependencies: ["pip-audit"]

Conclusion

Cette feuille de route décrit de manière exhaustive les actions à mener pour transformer le backend ERP MIF Maroc en une solution prête pour la production. En appliquant les correctifs obligatoires, en renforçant l’infrastructure et en adoptant une démarche DevOps (CI/CD, monitoring, sauvegardes), l’équipe pourra garantir la sécurité, la performance et la maintenabilité du système. L’atteinte des critères Go‑Prod permettra de prendre une décision éclairée et de déployer l’ERP en production avec un niveau de confiance élevé.
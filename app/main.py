# app/main.py

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.middleware import CorrelationIdMiddleware, register_exception_handlers
from app.core.config import settings
from app.core.logging import get_logger, setup_logging

# Optional scheduler
try:
    from app.tasks.scheduler import run_planning_generation, scheduler
except Exception:
    scheduler = None

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Optional scheduler
try:
    from app.tasks.scheduler import run_planning_generation, scheduler
except Exception:
    scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 {settings.PROJECT_NAME} démarré!")
    print("📚 Documentation disponible sur: http://localhost:8000/docs")
    # Start scheduler if enabled
    if getattr(settings, "ENABLE_SCHEDULER", False) and scheduler:
        try:
            # register the job if not already
            if not any(job.id == "planning_job" for job in scheduler.get_jobs()):
                scheduler.add_job(
                    run_planning_generation, "interval", hours=1, id="planning_job"
                )
            scheduler.start()
            print("⏱️ Scheduler started")
        except Exception as e:
            print(f"⚠️ Scheduler not started: {e}")
    try:
        yield
    finally:
        # Shutdown
        if getattr(settings, "ENABLE_SCHEDULER", False) and scheduler:
            try:
                scheduler.shutdown(wait=False)
                print("⏹️ Scheduler stopped")
            except Exception:
                pass
        print("👋 Arrêt de l'application...")


# Création de l'application FastAPI avec gestionnaire de cycle de vie
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend ERP pour la gestion des interventions industrielles",
    lifespan=lifespan,
)

if not settings.DEBUG and "*" in settings.CORS_ALLOW_ORIGINS:
    raise ValueError(
        "CORS_ALLOW_ORIGINS ne doit pas contenir '*' en production. Configurez des origines explicites."
    )

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=settings.CORS_EXPOSE_HEADERS,
)

# Gestion uniformisée des erreurs et identifiant de corrélation
app.add_middleware(CorrelationIdMiddleware)
register_exception_handlers(app)

# Rate limiting middleware
if not settings.DEBUG:  # Only in production
    from app.core.ratelimit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

# We want /static to point to the parent of the uploads dir so that
# /static/uploads/* is served
project_root = Path(__file__).resolve().parents[1]  # repo root
raw_upload = str(settings.UPLOAD_DIRECTORY)
configured = Path(raw_upload)

# Normalize configured path robustly
parts = configured.parts
root_indicators = (os.sep, "/", "\\")
starts_with_root = parts and parts[0] in root_indicators

# Case 1: values like "/app/static/uploads" or "\\app\\static\\uploads" from Docker .env
# -> map to project_root/app/static/uploads
if starts_with_root and len(parts) >= 2 and parts[1].lower() == "app":
    # On Windows, absolute paths starting with \app or /app are likely stray;
    # remap to project root.
    # On Linux (e.g., Docker), '/app/...' is the valid project root inside the
    # container; keep as-is.
    if os.name == "nt":
        configured = project_root.joinpath(*parts[1:])
# Case 2: relative path -> make it relative to project root
elif not configured.is_absolute():
    configured = project_root / configured

uploads_dir = configured.resolve()
# Ensure directories exist to avoid StaticFiles check_dir errors
uploads_dir.mkdir(parents=True, exist_ok=True)
static_root = uploads_dir.parent

# Propagate normalized absolute path back to settings so services use the same directory
try:
    settings.UPLOAD_DIRECTORY = str(uploads_dir)
except Exception:
    pass

app.mount(
    "/static", StaticFiles(directory=str(static_root), check_dir=True), name="static"
)

# Import des routes v1
try:
    from app.api.v1 import auth as auth
    from app.api.v1 import dashboard as dashboard
    from app.api.v1 import documents as documents
    from app.api.v1 import equipements as equipements
    from app.api.v1 import filters as filters
    from app.api.v1 import health as health
    from app.api.v1 import interventions as interventions
    from app.api.v1 import notifications as notifications
    from app.api.v1 import planning as planning
    from app.api.v1 import techniciens as techniciens
    from app.api.v1 import users as users

    api_prefix = settings.API_V1_STR
    # Mount under /api/v1/*
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(users.router, prefix=api_prefix)
    app.include_router(techniciens.router, prefix=api_prefix)
    app.include_router(equipements.router, prefix=api_prefix)
    app.include_router(interventions.router, prefix=api_prefix)
    app.include_router(planning.router, prefix=api_prefix)
    app.include_router(notifications.router, prefix=api_prefix)
    app.include_router(documents.router, prefix=api_prefix)
    app.include_router(filters.router, prefix=api_prefix)
    app.include_router(dashboard.router, prefix=api_prefix)
    app.include_router(health.router, prefix=api_prefix)
    # Backward-compatible mounts at root for existing tests/tools
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(techniciens.router)
    app.include_router(equipements.router)
    app.include_router(interventions.router)
    app.include_router(planning.router)
    app.include_router(notifications.router)
    app.include_router(documents.router)
    app.include_router(filters.router)
    app.include_router(dashboard.router)
    app.include_router(health.router)

except ImportError as e:
    print(f"Erreur lors de l'import des routes: {e}")
    print("Certaines routes peuvent ne pas être disponibles.")


# Route de base pour vérifier que l'API fonctionne
@app.get("/")
def read_root():
    return {
        "message": "Bienvenue sur l'API ERP MIF Maroc",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Les événements startup/shutdown sont maintenant gérés par lifespan ci-dessus

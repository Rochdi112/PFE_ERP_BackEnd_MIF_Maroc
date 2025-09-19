# app/api/v1/health.py

import redis
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from datetime import datetime

from app.api.middleware.observability import get_observability_middleware
from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import get_metrics, get_metrics_content_type
from app.db.database import get_db

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check():
    """Basic health check endpoint for load balancers"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
    }


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe - vérifie que l'app répond"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
    }


@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetes readiness probe - vérifie les dépendances"""
    health_status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "checks": {}
    }
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "not_ready"
    
    # Redis check (if configured)
    try:
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "not_configured",
                "message": "Redis not configured"
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
        # Redis n'est pas critique pour le readiness
    
    return health_status


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""
    
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "checks": {},
    }
    
    # Database check
    try:
        db.execute(text("SELECT version()"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
        health_status["status"] = "unhealthy"
    
    # Redis check (if configured)
    try:
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            redis_client = redis.from_url(settings.REDIS_URL)
            info = redis_client.info()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful",
                "version": info.get("redis_version", "unknown")
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "not_configured",
                "message": "Redis not configured",
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }
    
    # System metrics
    if PSUTIL_AVAILABLE:
        try:
            health_status["checks"]["system"] = {
                "status": "ok",
                "metrics": {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                },
            }
        except Exception as e:
            health_status["checks"]["system"] = {
                "status": "warning",
                "message": f"System metrics collection failed: {str(e)}",
            }
    else:
        health_status["checks"]["system"] = {
            "status": "warning",
            "message": "psutil not available, system metrics not included",
        }
    
    # Application metrics
    middleware = get_observability_middleware()
    if middleware:
        app_metrics = middleware.get_metrics()
        health_status["checks"]["application"] = {
            "status": "ok",
            "metrics": {
                "total_requests": app_metrics["total_requests"],
                "error_rate": app_metrics["error_rate"],
                "avg_response_time_ms": app_metrics["avg_duration_ms"],
                "p95_response_time_ms": app_metrics["p95_duration_ms"]
            }
        }
    
    # Log health check results
    if health_status["status"] == "unhealthy":
        logger.warning(
            "Health check failed",
            extra={"extra_fields": health_status}
        )
    
    return health_status


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-style metrics endpoint.
    Returns metrics in Prometheus exposition format.
    """
    # Les métriques Prometheus sont maintenant gérées par le service de métriques
    content = get_metrics()
    return Response(content=content, media_type=get_metrics_content_type())

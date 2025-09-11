# app/api/v1/health.py

import redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_db

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""

    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
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
        if hasattr(settings, "REDIS_URL"):
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful",
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
        health_status["checks"]["system"] = {
            "status": "ok",
            "metrics": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            },
        }
    else:
        health_status["checks"]["system"] = {
            "status": "warning",
            "message": "psutil not available, system metrics not included",
        }

    # Log health check results
    if health_status["status"] == "unhealthy":
        logger.warning("Health check failed", extra_fields=health_status)

    return health_status


@router.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    metrics_data = []

    # System metrics
    if PSUTIL_AVAILABLE:
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent

        metrics_data.append("# HELP erp_cpu_usage CPU usage percentage")
        metrics_data.append("# TYPE erp_cpu_usage gauge")
        metrics_data.append(f"erp_cpu_usage {cpu_percent}")

        metrics_data.append("# HELP erp_memory_usage Memory usage percentage")
        metrics_data.append("# TYPE erp_memory_usage gauge")
        metrics_data.append(f"erp_memory_usage {memory_percent}")

        metrics_data.append("# HELP erp_disk_usage Disk usage percentage")
        metrics_data.append("# TYPE erp_disk_usage gauge")
        metrics_data.append(f"erp_disk_usage {disk_percent}")
    else:
        metrics_data.append("# psutil not available, system metrics not included")

    return "\n".join(metrics_data)

# app/api/middleware/observability.py

"""
Middleware pour l'observabilité: métriques, timing, logs structurés.
"""

import time
from typing import Callable, Dict
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.metrics import metrics_service

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour l'observabilité complète:
    - Correlation ID
    - Request timing
    - Structured logging
    - Metrics collection
    """
    
    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name
        
        # Métriques en mémoire (en prod: Prometheus)
        self.request_count = 0
        self.request_durations = []
        self.error_count = 0
        self.endpoint_metrics: Dict[str, Dict] = {}
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        # Générer ou récupérer correlation ID
        incoming_id = request.headers.get(self.header_name)
        request_id = incoming_id or str(uuid4())
        request.state.request_id = request_id
        request.state.trace_id = request_id  # Compatibility
        
        # Démarrer le timing
        start_time = time.time()
        
        # Extraire les informations de requête
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Normaliser l'endpoint pour les métriques
        endpoint_for_metrics = self._normalize_endpoint(path)
        
        # Incrémenter compteur global
        self.request_count += 1
        
        # Commencer le suivi de la requête pour Prometheus
        metrics_service.start_http_request(method, endpoint_for_metrics)
        
        # Log de début de requête
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "event": "request_start"
                }
            }
        )
        
        # Traiter la requête
        response = None
        status_code = 500
        error_details = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            self.error_count += 1
            status_code = 500
            error_details = str(e)
            logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "error": error_details,
                        "event": "request_error"
                    }
                }
            )
            # Re-raise pour le gestionnaire d'erreurs
            raise
        
        finally:
            # Calculer la durée
            end_time = time.time()
            duration_ms = round((end_time - start_time) * 1000, 2)
            duration_seconds = (end_time - start_time)
            
            # Terminer le suivi de la requête pour Prometheus
            metrics_service.end_http_request(method, endpoint_for_metrics)
            
            # Enregistrer la requête dans Prometheus
            metrics_service.record_http_request(
                method, endpoint_for_metrics, status_code, duration_seconds
            )
            
            # Enregistrer la durée
            self.request_durations.append(duration_ms)
            
            # Maintenir seulement les 1000 dernières requêtes
            if len(self.request_durations) > 1000:
                self.request_durations = self.request_durations[-1000:]
            
            # Métriques par endpoint
            endpoint_key = f"{method} {path}"
            if endpoint_key not in self.endpoint_metrics:
                self.endpoint_metrics[endpoint_key] = {
                    "count": 0,
                    "durations": [],
                    "errors": 0
                }
            
            endpoint_data = self.endpoint_metrics[endpoint_key]
            endpoint_data["count"] += 1
            endpoint_data["durations"].append(duration_ms)
            
            if status_code >= 400:
                endpoint_data["errors"] += 1
            
            # Maintenir seulement les 100 dernières durées par endpoint
            if len(endpoint_data["durations"]) > 100:
                endpoint_data["durations"] = endpoint_data["durations"][-100:]
            
            # Log de fin de requête
            log_level = "warning" if status_code >= 400 else "info"
            
            log_data = {
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "event": "request_complete"
            }
            
            if error_details:
                log_data["error"] = error_details
            
            if log_level == "warning":
                logger.warning(
                    f"Request completed: {method} {path} [{status_code}] {duration_ms}ms",
                    extra={"extra_fields": log_data}
                )
            else:
                logger.info(
                    f"Request completed: {method} {path} [{status_code}] {duration_ms}ms",
                    extra={"extra_fields": log_data}
                )
        
        # Ajouter headers de réponse
        if response:
            response.headers.setdefault(self.header_name, request_id)
            response.headers.setdefault("X-Response-Time", f"{duration_ms}ms")
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalise l'endpoint pour les métriques (remplace les IDs par des placeholders)."""
        # Remplacer les IDs numériques par {id} pour éviter la cardinalité élevée
        import re
        # Remplacer /api/v1/users/123 par /api/v1/users/{id}
        normalized = re.sub(r'/\d+', '/{id}', path)
        
        # Limiter la longueur pour éviter l'explosion de cardinalité
        if len(normalized) > 100:
            normalized = normalized[:97] + "..."
        
        return normalized
    
    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'adresse IP du client."""
        # Vérifier les headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # IP directe
        return request.client.host if request.client else "unknown"
    
    def get_metrics(self) -> dict:
        """Retourne les métriques collectées."""
        total_requests = len(self.request_durations)
        
        # Calculs statistiques
        avg_duration = sum(self.request_durations) / total_requests if total_requests > 0 else 0
        
        # Percentiles approximatifs
        sorted_durations = sorted(self.request_durations)
        p50 = sorted_durations[int(total_requests * 0.5)] if total_requests > 0 else 0
        p95 = sorted_durations[int(total_requests * 0.95)] if total_requests > 0 else 0
        p99 = sorted_durations[int(total_requests * 0.99)] if total_requests > 0 else 0
        
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
            "avg_duration_ms": round(avg_duration, 2),
            "p50_duration_ms": p50,
            "p95_duration_ms": p95,
            "p99_duration_ms": p99,
            "endpoints": {
                endpoint: {
                    "count": data["count"],
                    "errors": data["errors"],
                    "error_rate": (data["errors"] / data["count"] * 100) if data["count"] > 0 else 0,
                    "avg_duration_ms": round(sum(data["durations"]) / len(data["durations"]), 2) if data["durations"] else 0
                }
                for endpoint, data in self.endpoint_metrics.items()
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Retourne les métriques au format Prometheus."""
        metrics = self.get_metrics()
        lines = []
        
        # Métriques globales
        lines.append("# HELP http_requests_total Total number of HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        lines.append(f"http_requests_total {metrics['total_requests']}")
        
        lines.append("# HELP http_errors_total Total number of HTTP errors")
        lines.append("# TYPE http_errors_total counter")
        lines.append(f"http_errors_total {metrics['total_errors']}")
        
        lines.append("# HELP http_request_duration_ms Request duration in milliseconds")
        lines.append("# TYPE http_request_duration_ms histogram")
        lines.append(f"http_request_duration_ms_sum {sum(self.request_durations)}")
        lines.append(f"http_request_duration_ms_count {len(self.request_durations)}")
        
        # Buckets de latence
        buckets = [10, 50, 100, 200, 500, 1000, 2000, 5000]
        for bucket in buckets:
            count = len([d for d in self.request_durations if d <= bucket])
            lines.append(f'http_request_duration_ms_bucket{{le="{bucket}"}} {count}')
        lines.append(f'http_request_duration_ms_bucket{{le="+Inf"}} {len(self.request_durations)}')
        
        # Métriques par endpoint
        lines.append("# HELP http_requests_by_endpoint Requests by endpoint")
        lines.append("# TYPE http_requests_by_endpoint counter")
        for endpoint, data in metrics["endpoints"].items():
            method, path = endpoint.split(" ", 1)
            lines.append(f'http_requests_by_endpoint{{method="{method}",path="{path}"}} {data["count"]}')
        
        return "\n".join(lines)


# Instance globale pour collecter les métriques
observability_middleware = None


def get_observability_middleware() -> ObservabilityMiddleware:
    """Retourne l'instance du middleware d'observabilité."""
    global observability_middleware
    return observability_middleware


def set_observability_middleware(middleware: ObservabilityMiddleware):
    """Définit l'instance du middleware d'observabilité."""
    global observability_middleware
    observability_middleware = middleware
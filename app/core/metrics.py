# app/core/metrics.py

"""
Service de métriques Prometheus pour observabilité Go-Prod.
"""

from typing import Dict, Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsService:
    """Service de collecte et exposition des métriques Prometheus."""
    
    def __init__(self):
        self.metrics_initialized = False
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialise les métriques Prometheus."""
        
        # Métriques HTTP
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.http_requests_in_progress = Gauge(
            'http_requests_in_progress',
            'Number of HTTP requests currently in progress',
            ['method', 'endpoint']
        )
        
        # Métriques d'application
        self.app_info = Gauge(
            'app_info',
            'Application information',
            ['service', 'version', 'environment']
        )
        
        # Métriques de base de données
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections'
        )
        
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total number of database queries',
            ['query_type', 'status']
        )
        
        # Métriques d'authentification
        self.auth_attempts_total = Counter(
            'auth_attempts_total',
            'Total number of authentication attempts',
            ['status', 'method']
        )
        
        self.auth_tokens_active = Gauge(
            'auth_tokens_active',
            'Number of active authentication tokens'
        )
        
        # Métriques de sécurité
        self.security_events_total = Counter(
            'security_events_total',
            'Total number of security events',
            ['event_type', 'severity']
        )
        
        self.failed_login_attempts = Counter(
            'failed_login_attempts_total',
            'Total number of failed login attempts',
            ['reason', 'ip_address']
        )
        
        # Métriques business
        self.interventions_total = Counter(
            'interventions_total',
            'Total number of interventions',
            ['status', 'type']
        )
        
        self.documents_total = Counter(
            'documents_total',
            'Total number of documents',
            ['type', 'encrypted']
        )
        
        # Métriques système (initialisées avec des valeurs par défaut)
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage'
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_percent',
            'System disk usage percentage'
        )
        
        # Initialiser les métriques d'info
        self.app_info.labels(
            service=settings.PROJECT_NAME,
            version="1.0.0",
            environment=settings.ENVIRONMENT
        ).set(1)
        
        self.metrics_initialized = True
        logger.info("Métriques Prometheus initialisées")
    
    # Méthodes pour HTTP
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Enregistre une requête HTTP."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def start_http_request(self, method: str, endpoint: str):
        """Marque le début d'une requête HTTP."""
        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()
    
    def end_http_request(self, method: str, endpoint: str):
        """Marque la fin d'une requête HTTP."""
        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()
    
    # Méthodes pour la base de données
    def record_db_query(self, query_type: str, duration: float, success: bool = True):
        """Enregistre une requête de base de données."""
        status = "success" if success else "error"
        
        self.db_queries_total.labels(
            query_type=query_type,
            status=status
        ).inc()
        
        self.db_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)
    
    def set_db_connections(self, count: int):
        """Met à jour le nombre de connexions DB actives."""
        self.db_connections_active.set(count)
    
    # Méthodes pour l'authentification
    def record_auth_attempt(self, success: bool, method: str = "password"):
        """Enregistre une tentative d'authentification."""
        status = "success" if success else "failure"
        self.auth_attempts_total.labels(
            status=status,
            method=method
        ).inc()
    
    def set_active_tokens(self, count: int):
        """Met à jour le nombre de tokens actifs."""
        self.auth_tokens_active.set(count)
    
    # Méthodes pour la sécurité
    def record_security_event(self, event_type: str, severity: str = "info"):
        """Enregistre un événement de sécurité."""
        self.security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    def record_failed_login(self, reason: str, ip_address: str):
        """Enregistre une tentative de connexion échouée."""
        # Anonymiser l'IP pour la vie privée (garder seulement les 3 premiers octets)
        ip_parts = ip_address.split('.')
        if len(ip_parts) == 4:
            anonymized_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.xxx"
        else:
            anonymized_ip = "unknown"
        
        self.failed_login_attempts.labels(
            reason=reason,
            ip_address=anonymized_ip
        ).inc()
    
    # Méthodes business
    def record_intervention(self, status: str, intervention_type: str):
        """Enregistre une intervention."""
        self.interventions_total.labels(
            status=status,
            type=intervention_type
        ).inc()
    
    def record_document(self, doc_type: str, encrypted: bool = True):
        """Enregistre un document."""
        self.documents_total.labels(
            type=doc_type,
            encrypted="yes" if encrypted else "no"
        ).inc()
    
    # Méthodes système
    def update_system_metrics(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Met à jour les métriques système."""
        self.system_cpu_usage.set(cpu_percent)
        self.system_memory_usage.set(memory_percent)
        self.system_disk_usage.set(disk_percent)
    
    def get_metrics_content(self) -> bytes:
        """Retourne les métriques au format Prometheus."""
        return generate_latest()
    
    def get_content_type(self) -> str:
        """Retourne le content-type pour les métriques Prometheus."""
        return CONTENT_TYPE_LATEST


# Instance globale
metrics_service = MetricsService()


# Fonctions utilitaires
def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Fonction utilitaire pour enregistrer une requête HTTP."""
    metrics_service.record_http_request(method, endpoint, status_code, duration)


def start_http_request(method: str, endpoint: str):
    """Fonction utilitaire pour marquer le début d'une requête HTTP."""
    metrics_service.start_http_request(method, endpoint)


def end_http_request(method: str, endpoint: str):
    """Fonction utilitaire pour marquer la fin d'une requête HTTP."""
    metrics_service.end_http_request(method, endpoint)


def record_auth_attempt(success: bool, method: str = "password"):
    """Fonction utilitaire pour enregistrer une tentative d'auth."""
    metrics_service.record_auth_attempt(success, method)


def record_security_event(event_type: str, severity: str = "info"):
    """Fonction utilitaire pour enregistrer un événement de sécurité."""
    metrics_service.record_security_event(event_type, severity)


def get_metrics() -> bytes:
    """Fonction utilitaire pour obtenir les métriques."""
    return metrics_service.get_metrics_content()


def get_metrics_content_type() -> str:
    """Fonction utilitaire pour obtenir le content-type des métriques."""
    return metrics_service.get_content_type()
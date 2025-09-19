# app/core/tracing.py

"""
Configuration OpenTelemetry pour traçage distribué Go-Prod.
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TracingService:
    """Service de configuration OpenTelemetry."""
    
    def __init__(self):
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer = None
        self.instrumented = False
    
    def initialize_tracing(self, app=None):
        """
        Initialise OpenTelemetry avec instrumentation automatique.
        
        Args:
            app: Instance FastAPI (optionnel pour instrumentation)
        """
        if self.instrumented:
            logger.info("Tracing déjà initialisé")
            return
        
        try:
            # Configuration du service resource
            resource = Resource.create({
                "service.name": settings.PROJECT_NAME,
                "service.version": "1.0.0",
                "service.instance.id": os.getenv("HOSTNAME", "unknown"),
                "deployment.environment": settings.ENVIRONMENT,
            })
            
            # Créer le tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Configurer les exporters
            self._configure_exporters()
            
            # Instrumentation automatique
            self._setup_instrumentations(app)
            
            # Obtenir le tracer
            self.tracer = trace.get_tracer(__name__)
            
            self.instrumented = True
            logger.info("OpenTelemetry initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation OpenTelemetry: {e}")
            # Continuer sans tracing en cas d'erreur
    
    def _configure_exporters(self):
        """Configure les exporters de spans."""
        
        # OTLP Exporter (Jaeger, etc.)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    headers=(
                        {"authorization": f"Bearer {os.getenv('OTEL_EXPORTER_OTLP_HEADERS')}"}
                        if os.getenv('OTEL_EXPORTER_OTLP_HEADERS')
                        else {}
                    ),
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(span_processor)
                logger.info(f"OTLP exporter configuré: {otlp_endpoint}")
                
            except Exception as e:
                logger.warning(f"Impossible de configurer l'exporter OTLP: {e}")
        
        # Console exporter pour développement
        if settings.DEBUG:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(console_processor)
            logger.info("Console exporter activé (mode debug)")
    
    def _setup_instrumentations(self, app=None):
        """Configure l'instrumentation automatique."""
        
        try:
            # FastAPI instrumentation
            if app:
                FastAPIInstrumentor.instrument_app(
                    app,
                    tracer_provider=self.tracer_provider,
                    excluded_urls="/health,/live,/ready,/metrics",  # Exclure les endpoints de monitoring
                )
                logger.info("Instrumentation FastAPI activée")
            
            # SQLAlchemy instrumentation
            SQLAlchemyInstrumentor().instrument(
                tracer_provider=self.tracer_provider,
                enable_commenter=True,  # Ajouter des commentaires SQL avec trace ID
            )
            logger.info("Instrumentation SQLAlchemy activée")
            
            # Requests instrumentation
            RequestsInstrumentor().instrument(tracer_provider=self.tracer_provider)
            logger.info("Instrumentation Requests activée")
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'instrumentation: {e}")
    
    def get_tracer(self):
        """Retourne le tracer OpenTelemetry."""
        if not self.tracer:
            self.tracer = trace.get_tracer(__name__)
        return self.tracer
    
    def create_span(self, name: str, **kwargs):
        """Crée un span personnalisé."""
        if not self.tracer:
            return None
        return self.tracer.start_span(name, **kwargs)
    
    def add_span_attributes(self, span, attributes: dict):
        """Ajoute des attributs à un span."""
        if span:
            for key, value in attributes.items():
                span.set_attribute(key, value)
    
    def record_exception(self, span, exception: Exception):
        """Enregistre une exception dans un span."""
        if span:
            span.record_exception(exception)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
    
    def shutdown(self):
        """Ferme proprement le tracing."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Tracing fermé")


# Instance globale
tracing_service = TracingService()


def get_tracer():
    """Fonction utilitaire pour obtenir le tracer."""
    return tracing_service.get_tracer()


def create_span(name: str, **kwargs):
    """Fonction utilitaire pour créer un span."""
    return tracing_service.create_span(name, **kwargs)


def initialize_tracing(app=None):
    """Fonction utilitaire pour initialiser le tracing."""
    tracing_service.initialize_tracing(app)


def shutdown_tracing():
    """Fonction utilitaire pour fermer le tracing."""
    tracing_service.shutdown()